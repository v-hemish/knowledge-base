
import swisseph as swe

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

def zodiac_sign(longitude: float) -> tuple[str, float]:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30
    return signs[sign_index], degree_in_sign


jd = swe.julday(1999, 6, 29, 4.5)

for name, planet_id in PLANETS.items():
    result, flags = swe.calc_ut(jd, planet_id)
    lon = result[0]
    sign, deg = zodiac_sign(lon)
    print(f"{name:8} {lon:8.4f}°   {sign} {deg:.2f}°")
    
    