"""Curated electronics catalog for offline demo-quality recommendations.

The raw Amazon electronics review datasets in `data/raw/recommendation` do not
always contain product titles/brands. This curated catalog is used as a
fallback so the Streamlit demo can return realistic item names offline.
"""

from __future__ import annotations

from typing import Dict, List

ELECTRONICS_CATALOG: Dict[str, List[dict]] = {
    "phones": [
        {
            "itemId": "phone_pixel_7a",
            "title": "Google Pixel 7a",
            "price": 499,
            "rating": 4.6,
            "popularity": 9000,
            "tags": ["google", "pixel", "android", "camera", "budget", "5g"],
        },
        {
            "itemId": "phone_galaxy_a54",
            "title": "Samsung Galaxy A54 5G",
            "price": 449,
            "rating": 4.5,
            "popularity": 8500,
            "tags": ["samsung", "galaxy", "android", "battery", "budget", "5g"],
        },
        {
            "itemId": "phone_iphone_se_3",
            "title": "iPhone SE (3rd gen)",
            "price": 429,
            "rating": 4.4,
            "popularity": 7800,
            "tags": ["apple", "iphone", "ios", "budget", "compact"],
        },
        {
            "itemId": "phone_oneplus_nord_n30",
            "title": "OnePlus Nord N30 5G",
            "price": 299,
            "rating": 4.3,
            "popularity": 6200,
            "tags": ["oneplus", "nord", "android", "budget", "5g"],
        },
        {
            "itemId": "phone_moto_g_power",
            "title": "Motorola Moto G Power",
            "price": 249,
            "rating": 4.2,
            "popularity": 5400,
            "tags": ["motorola", "moto", "android", "battery", "budget"],
        },
        {
            "itemId": "phone_galaxy_s23_fe",
            "title": "Samsung Galaxy S23 FE",
            "price": 599,
            "rating": 4.5,
            "popularity": 5100,
            "tags": ["samsung", "galaxy", "android", "camera", "5g"],
        },
    ],
    "laptops": [
        {
            "itemId": "laptop_dell_inspiron_14",
            "title": "Dell Inspiron 14",
            "price": 799,
            "rating": 4.3,
            "popularity": 6900,
            "tags": ["dell", "inspiron", "programming", "budget", "intel", "ssd"],
        },
        {
            "itemId": "laptop_lenovo_thinkpad_e14",
            "title": "Lenovo ThinkPad E14",
            "price": 899,
            "rating": 4.5,
            "popularity": 7200,
            "tags": ["lenovo", "thinkpad", "programming", "business", "keyboard", "ssd"],
        },
        {
            "itemId": "laptop_macbook_air_m2",
            "title": "MacBook Air (M2)",
            "price": 1099,
            "rating": 4.8,
            "popularity": 12000,
            "tags": ["apple", "macbook", "programming", "battery", "portable"],
        },
        {
            "itemId": "laptop_asus_zenbook_14",
            "title": "ASUS ZenBook 14",
            "price": 999,
            "rating": 4.4,
            "popularity": 5300,
            "tags": ["asus", "zenbook", "programming", "portable", "ssd"],
        },
        {
            "itemId": "laptop_acer_swift_3",
            "title": "Acer Swift 3",
            "price": 749,
            "rating": 4.2,
            "popularity": 6100,
            "tags": ["acer", "swift", "programming", "budget", "portable", "ssd"],
        },
        {
            "itemId": "laptop_hp_pavilion_15",
            "title": "HP Pavilion 15",
            "price": 699,
            "rating": 4.1,
            "popularity": 5600,
            "tags": ["hp", "pavilion", "programming", "budget", "intel"],
        },
    ],
    "headphones": [
        {
            "itemId": "hp_sony_wh_1000xm5",
            "title": "Sony WH-1000XM5",
            "price": 399,
            "rating": 4.8,
            "popularity": 15000,
            "tags": ["sony", "noise", "cancelling", "wireless", "bluetooth"],
        },
        {
            "itemId": "hp_bose_qc45",
            "title": "Bose QuietComfort 45",
            "price": 329,
            "rating": 4.6,
            "popularity": 11000,
            "tags": ["bose", "noise", "cancelling", "wireless", "bluetooth"],
        },
        {
            "itemId": "hp_airpods_pro_2",
            "title": "Apple AirPods Pro (2nd gen)",
            "price": 249,
            "rating": 4.7,
            "popularity": 17000,
            "tags": ["apple", "airpods", "earbuds", "noise", "cancelling", "wireless"],
        },
        {
            "itemId": "hp_soundcore_q30",
            "title": "Anker Soundcore Life Q30",
            "price": 79,
            "rating": 4.4,
            "popularity": 19000,
            "tags": ["anker", "soundcore", "budget", "noise", "cancelling", "wireless"],
        },
        {
            "itemId": "hp_sennheiser_hd560s",
            "title": "Sennheiser HD 560S",
            "price": 199,
            "rating": 4.6,
            "popularity": 4200,
            "tags": ["sennheiser", "wired", "studio", "audio"],
        },
        {
            "itemId": "hp_sony_wf_1000xm5",
            "title": "Sony WF-1000XM5",
            "price": 299,
            "rating": 4.6,
            "popularity": 6000,
            "tags": ["sony", "earbuds", "noise", "cancelling", "wireless"],
        },
    ],
    "cameras": [
        {
            "itemId": "cam_canon_eos_r50",
            "title": "Canon EOS R50",
            "price": 679,
            "rating": 4.6,
            "popularity": 4200,
            "tags": ["canon", "camera", "mirrorless", "vlog", "4k"],
        },
        {
            "itemId": "cam_sony_alpha_a6400",
            "title": "Sony Alpha a6400",
            "price": 898,
            "rating": 4.7,
            "popularity": 5100,
            "tags": ["sony", "camera", "mirrorless", "aps-c", "4k"],
        },
        {
            "itemId": "cam_nikon_z30",
            "title": "Nikon Z30",
            "price": 749,
            "rating": 4.5,
            "popularity": 3300,
            "tags": ["nikon", "camera", "mirrorless", "vlog", "compact"],
        },
        {
            "itemId": "cam_fujifilm_xs10",
            "title": "Fujifilm X-S10",
            "price": 999,
            "rating": 4.6,
            "popularity": 2800,
            "tags": ["fujifilm", "camera", "mirrorless", "stabilization", "aps-c"],
        },
        {
            "itemId": "cam_panasonic_g7",
            "title": "Panasonic Lumix G7",
            "price": 597,
            "rating": 4.4,
            "popularity": 3900,
            "tags": ["panasonic", "camera", "mirrorless", "mft", "4k"],
        },
        {
            "itemId": "cam_canon_rebel_t7",
            "title": "Canon EOS Rebel T7",
            "price": 479,
            "rating": 4.3,
            "popularity": 4700,
            "tags": ["canon", "camera", "dslr", "starter", "photo"],
        },
    ],
}


__all__ = ["ELECTRONICS_CATALOG"]
