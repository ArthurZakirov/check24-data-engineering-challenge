def extract_rating(card):
    rating = 0.0
    for star in card.select(".product-rating .product-review-point .point-rating"):
        classes = star.get("class", [])
        if "point-full" in classes:
            rating += 1
        elif "point-partial" in classes:
            rating += 0.5
            style = star.get("style") or ""
            if "clip-path" in style:
                import re
                m = re.search(r"inset\(0\s+(\d+)%", style)
                if m:
                    right_cut = int(m.group(1))   
                    frac = (100 - right_cut) / 100
                    rating += (frac - 0.5)  
    return rating
