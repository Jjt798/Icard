from PIL import Image, ImageDraw, ImageFont, ImageOps
def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, float) and value != value:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False

def _clean(value):
    return "" if _is_missing(value) else value

def _load_font(bold, size):
    candidates = (
        ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else
        ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _fit_title_font(draw, text, bold, max_width, start_size=30, min_size=16):
    size = start_size
    while size > min_size:
        font = _load_font(bold, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _load_font(bold, min_size)

def _wrap_text(draw, text, font, max_width, max_lines=2):
    text = str(text)
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    lines.append(current)
    remaining_words = words[len(" ".join(lines).split()):]
    if remaining_words or draw.textlength(lines[-1], font=font) > max_width:
        last = lines[-1]
        while draw.textlength(last + "...", font=font) > max_width and len(last) > 1:
            last = last[:-1].rstrip()
        lines[-1] = last + "..."
    return lines[:max_lines]

def create_id_card(student, school):
    WIDTH = 650
    HEIGHT = 470
    card = Image.new("RGB", (WIDTH, HEIGHT), "#F5F9FF")
    draw = ImageDraw.Draw(card)
    title_font = _load_font(True, 30)
    address_font = _load_font(False, 16)
    label_font = _load_font(True, 20)
    value_font = _load_font(False, 20)
    small_font = _load_font(False, 14)
    HEADER_H = 100
    BORDER = 18
    draw.rectangle([(0, 0), (WIDTH, HEADER_H)], fill="#1976D2")
    LOGO_SIZE = 80
    logo_x = 35
    logo_y = (HEADER_H - LOGO_SIZE) // 2
    logo_drawn = False
    if school.get("logo") is not None:
        try:
            logo = Image.open(school["logo"]).convert("RGBA")
            logo.thumbnail((LOGO_SIZE, LOGO_SIZE))
            paste_x = logo_x + (LOGO_SIZE - logo.width) // 2
            paste_y = logo_y + (LOGO_SIZE - logo.height) // 2
            card.paste(logo, (paste_x, paste_y), logo)
            logo_drawn = True
        except Exception:
            logo_drawn = False
    if not logo_drawn:
        draw.rectangle(
            [(logo_x, logo_y), (logo_x + LOGO_SIZE, logo_y + LOGO_SIZE)],
            outline="white",
            width=1
        )
        draw.text(
            (logo_x + LOGO_SIZE // 2, logo_y + LOGO_SIZE // 2),
            "LOGO",
            font=small_font,
            fill="white",
            anchor="mm"
        )
 
    # ---- school name + school address (fixed) ----
    school_name = str(_clean(school.get("name", "")))
    school_address = str(_clean(school.get("address", "")))
    session = str(_clean(school.get("session", "")))
 
    text_left = logo_x + LOGO_SIZE + 15       # left edge of the space available for text
    text_right = WIDTH - 15
    text_max_width = text_right - text_left
    text_center_x = (text_left + text_right) / 2   # centered within remaining header space
 
    fitted_title_font = _fit_title_font(
        draw, school_name, True, text_max_width, start_size=36, min_size=14
    )
    draw.text(
        (text_center_x, HEADER_H * 0.30),
        school_name,
        font=fitted_title_font,
        fill="white",
        anchor="mm"
    )
 
    if school_address:
        fitted_address_font = _fit_title_font(
            draw, school_address, False, text_max_width, start_size=24, min_size=10
        )
        draw.text(
            (text_center_x, HEADER_H * 0.80),
            school_address,
            font=fitted_address_font,
            fill="white",
            anchor="mm"
        )
    # ---- end school name + school address ----
 
    photo_left = 20
    photo_top = 180
    photo_width = 170
    photo_height = 200
    draw.rectangle(
        [(photo_left, photo_top), (photo_left + photo_width, photo_top + photo_height)],
        outline="black",
        width=3
    )
    photo = student.get("photo")
    if not _is_missing(photo):
        try:
            photo_img = Image.open(photo).convert("RGB")
            photo_img = ImageOps.fit(
                photo_img,
                (photo_width - 6, photo_height - 6),
                method=Image.Resampling.LANCZOS
            )
            card.paste(photo_img, (photo_left + 3, photo_top + 3))
        except Exception:
            draw.text(
                (photo_left + photo_width // 2, photo_top + photo_height // 2),
                "PHOTO",
                font=label_font,
                fill="gray",
                anchor="mm"
            )
    else:
        draw.text(
            (photo_left + photo_width // 2, photo_top + photo_height // 2),
            "PHOTO",
            font=label_font,
            fill="gray",
            anchor="mm"
        )
    
    sign_area_x = photo_left
    sign_area_width = photo_width
    sign_area_height = 70
    sign_area_y = HEIGHT - BORDER - 50 - sign_area_height
    sign_label_y = HEIGHT - BORDER - 5
    
    # ---- Principal Signature ----
    sign_area_x = photo_left
    sign_area_width = photo_width

    SIGN_WIDTH = 130
    SIGN_HEIGHT = 55

    sign_x = sign_area_x + (sign_area_width - SIGN_WIDTH) // 2
    sign_y = HEIGHT - BORDER - 50

    signature_drawn = False

    if school.get("signature") is not None:
        try:
            sign = Image.open(school["signature"]).convert("RGBA")
            sign.thumbnail(
                (SIGN_WIDTH, SIGN_HEIGHT),
                Image.Resampling.LANCZOS
            )

            paste_x = sign_area_x + (sign_area_width - sign.width) // 2
            paste_y = sign_y + (SIGN_HEIGHT - sign.height) // 2

            card.paste(sign, (paste_x, paste_y), sign)

            signature_drawn = True

        except Exception:
            signature_drawn = False

    sign_label_y = HEIGHT - BORDER - 5

    draw.text(
        (sign_area_x + sign_area_width // 2, sign_label_y),
        "Principal",
        font=address_font,
        fill="black",
        anchor="mm"
    )
        
    draw.text(
        (sign_area_x + sign_area_width // 2, sign_label_y),
        "Principal",
        font=address_font,
        fill="black",
        anchor="mm"
    )
    x_label = 220
    x_colon = 310
    x_value = 342
    max_value_width = (WIDTH - BORDER - 10) - x_value
    line_height = 22
    y = 140
    row_gap = 30
 
    session = _clean(school.get("session", ""))
    if session:
        session_font = _load_font(True, 20)
        draw.text(
            (230, 130),
            f"Session : {session}",
            font=session_font,
            fill="red",
            anchor="la"
        )
        y += 28
 
    details = [
        ("SR No", _clean(student.get("sr", "")), 1),
        ("Name", _clean(student.get("name", "")), 2),
        ("Father", _clean(student.get("father", "")), 2),
        ("Mother", _clean(student.get("mother", "")), 2),
        ("Class", _clean(student.get("class", "")), 1),
        ("DOB", _clean(student.get("dob", "")), 1),
        ("Phone", _clean(student.get("phone", "")), 1),
        ("Address", _clean(student.get("address", "")), 3)
    ]
    for label, value, max_lines in details:
        draw.text((x_label, y), label, font=label_font, fill="black", anchor="la")
        draw.text((x_colon, y), ":", font=label_font, fill="black", anchor="la")
        lines = _wrap_text(draw, value, value_font, max_value_width, max_lines=max_lines)
        line_y = y
        for line in lines:
            draw.text((x_value, line_y), line, font=value_font, fill="#0D47A1", anchor="la")
            line_y += line_height
        row_height = max(row_gap, len(lines) * line_height + 6)
        y += row_height
    return card
if __name__ == "__main__":
    student = {
        "sr": 1,
        "name": "Alexander Christopher Whitmore",
        "father": "Jonathan Whitmore",
        "class": "10-A",
        "dob": "01-01-1970",
        "phone": "9876543210",
        "address": "221B Baker Street, Near City Park, Metropolis",
        "photo": None,
    }
    school = {
        "name": "Greenwood Public School",
        "address": "MG Road, Springfield",
        "logo": None,
        "signature": None,
    }
    card = create_id_card(student, school)
    card.save("/home/claude/id_card_preview.png")
    print("saved")
 











