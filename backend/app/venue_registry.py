from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


VENUE_FIELD_NAMES = tuple(
    """
venue_external_id venue_name venue_slug venue_category_primary venue_categories alternative_names description
street_address address_line_2 postcode town municipality province country latitude longitude geocode_precision
geocode_source google_maps_url openstreetmap_url website_url general_email general_phone booking_email booking_phone
manager_name manager_email manager_phone indoor_outdoor covered_available surface_types site_area_notes
number_of_entrances number_of_exits fenced lighting_available security_cameras vendor_entrance_notes loading_area_notes
vehicle_access trailer_access height_restrictions weight_restrictions setup_access_notes parking_available
parking_capacity_notes vendor_parking_notes overnight_parking_allowed camping_allowed public_transport_notes
nearest_train_station nearest_bus_stop bicycle_parking_available electricity_available electricity_connection_notes
electricity_connection_count max_electrical_load three_phase_available water_available water_connection_notes
waste_water_disposal grey_water_disposal waste_disposal recycling_available toilets_available accessible_toilets
showers_available wifi_available mobile_signal_notes lpg_allowed generator_allowed fire_safety_notes
food_vendor_suitability food_vendors_permitted typical_pitch_width_m typical_pitch_depth_m typical_pitch_notes
queue_space_notes seating_nearby power_reliability_notes water_proximity_notes cleaning_fee_policy deposit_policy
parking_fee_policy utility_pricing_policy wheelchair_accessible accessibility_notes wind_exposure shade_availability
drainage_quality flood_risk sun_exposure_notes weather_exposure_notes site_map_url vendor_map_url utility_map_url
parking_map_url emergency_plan_url fire_regulations_url food_regulations_url photo_gallery_url source_url_primary
source_url_secondary source_title_primary last_researched_at last_verified_at research_status confidence_rating
data_owner_notes internal_notes active
""".split()
)


SECTIONS: dict[str, tuple[str, ...]] = {
    "Identity": (
        "venue_external_id", "venue_name", "venue_slug", "venue_category_primary", "venue_categories",
        "alternative_names", "description", "active",
    ),
    "Address & map": (
        "street_address", "address_line_2", "postcode", "town", "municipality", "province", "country",
        "latitude", "longitude", "geocode_precision", "geocode_source", "google_maps_url", "openstreetmap_url",
        "website_url",
    ),
    "Contacts": (
        "general_email", "general_phone", "booking_email", "booking_phone", "manager_name", "manager_email",
        "manager_phone",
    ),
    "Site": (
        "indoor_outdoor", "covered_available", "surface_types", "site_area_notes", "number_of_entrances",
        "number_of_exits", "fenced", "lighting_available", "security_cameras",
    ),
    "Access & parking": (
        "vendor_entrance_notes", "loading_area_notes", "vehicle_access", "trailer_access", "height_restrictions",
        "weight_restrictions", "setup_access_notes", "parking_available", "parking_capacity_notes",
        "vendor_parking_notes", "overnight_parking_allowed", "camping_allowed",
    ),
    "Transport": (
        "public_transport_notes", "nearest_train_station", "nearest_bus_stop", "bicycle_parking_available",
    ),
    "Utilities": (
        "electricity_available", "electricity_connection_notes", "electricity_connection_count",
        "max_electrical_load", "three_phase_available", "water_available", "water_connection_notes",
        "waste_water_disposal", "grey_water_disposal", "waste_disposal", "recycling_available",
        "toilets_available", "accessible_toilets", "showers_available", "wifi_available", "mobile_signal_notes",
    ),
    "Safety": ("lpg_allowed", "generator_allowed", "fire_safety_notes"),
    "Vendor suitability": (
        "food_vendor_suitability", "food_vendors_permitted", "typical_pitch_width_m", "typical_pitch_depth_m",
        "typical_pitch_notes", "queue_space_notes", "seating_nearby", "power_reliability_notes",
        "water_proximity_notes",
    ),
    "Fees": ("cleaning_fee_policy", "deposit_policy", "parking_fee_policy", "utility_pricing_policy"),
    "Accessibility": ("wheelchair_accessible", "accessibility_notes"),
    "Weather": (
        "wind_exposure", "shade_availability", "drainage_quality", "flood_risk", "sun_exposure_notes",
        "weather_exposure_notes",
    ),
    "Documents": (
        "site_map_url", "vendor_map_url", "utility_map_url", "parking_map_url", "emergency_plan_url",
        "fire_regulations_url", "food_regulations_url", "photo_gallery_url",
    ),
    "Research": (
        "source_url_primary", "source_url_secondary", "source_title_primary", "last_researched_at",
        "last_verified_at", "research_status", "confidence_rating", "data_owner_notes", "internal_notes",
    ),
}

FIELD_SECTION = {field: section for section, fields in SECTIONS.items() for field in fields}

INTEGER_FIELDS = {"number_of_entrances", "number_of_exits", "electricity_connection_count"}
DECIMAL_FIELDS = {"latitude", "longitude", "typical_pitch_width_m", "typical_pitch_depth_m"}
DATE_FIELDS = {"last_researched_at", "last_verified_at"}
BOOLEAN_FIELDS = {"active"}
TEXTAREA_FIELDS = {
    name for name in VENUE_FIELD_NAMES
    if name.endswith("_notes") or name in {"description", "data_owner_notes", "internal_notes", "fire_safety_notes"}
}
URL_FIELDS = {name for name in VENUE_FIELD_NAMES if name.endswith("_url") or "_url_" in name}
EMAIL_FIELDS = {name for name in VENUE_FIELD_NAMES if name.endswith("_email")}
PHONE_FIELDS = {name for name in VENUE_FIELD_NAMES if name.endswith("_phone")}
MULTIVALUE_FIELDS = {"venue_categories", "alternative_names", "surface_types"}

ENUMS: dict[str, tuple[str, ...]] = {
    "venue_category_primary": (
        "town_square", "market_square", "fairground", "sports_complex", "stadium", "event_hall", "museum",
        "attraction", "park", "castle", "farm", "campground", "shopping_centre", "industrial_site", "school",
        "university", "harbour", "airport", "other",
    ),
    "geocode_precision": ("exact", "entrance", "venue_centroid", "street", "town_or_area", "unknown"),
    "geocode_source": ("official", "openstreetmap", "google_maps", "manual", "inferred", "unknown"),
    "research_status": ("discovered", "identified", "researched", "verified", "complete", "archived"),
    "confidence_rating": ("A", "B", "C", "D", "E"),
    "food_vendor_suitability": ("excellent", "good", "fair", "poor", "unknown"),
    "wind_exposure": ("low", "medium", "high", "unknown"),
    "shade_availability": ("none", "limited", "moderate", "good", "unknown"),
    "drainage_quality": ("poor", "fair", "good", "unknown"),
    "flood_risk": ("low", "medium", "high", "unknown"),
    "indoor_outdoor": ("indoor", "outdoor", "mixed", "unknown"),
}

YES_NO_UNKNOWN = {
    "fenced", "lighting_available", "security_cameras", "three_phase_available", "recycling_available",
    "toilets_available", "accessible_toilets", "showers_available", "lpg_allowed", "generator_allowed",
    "wheelchair_accessible",
}
YES_NO_LIMITED_UNKNOWN = {
    "covered_available", "parking_available", "bicycle_parking_available", "electricity_available",
    "water_available", "waste_disposal", "wifi_available", "seating_nearby",
}
YES_NO_RESTRICTED_UNKNOWN = {"vehicle_access", "trailer_access"}
YES_NO_PERMISSION_UNKNOWN = {"overnight_parking_allowed", "camping_allowed"}
YES_NO_DEPENDS_UNKNOWN = {"food_vendors_permitted"}

for field in YES_NO_UNKNOWN:
    ENUMS[field] = ("yes", "no", "unknown")
for field in YES_NO_LIMITED_UNKNOWN:
    ENUMS[field] = ("yes", "no", "limited", "unknown")
for field in YES_NO_RESTRICTED_UNKNOWN:
    ENUMS[field] = ("yes", "no", "restricted", "unknown")
for field in YES_NO_PERMISSION_UNKNOWN:
    ENUMS[field] = ("yes", "no", "with_permission", "unknown")
for field in YES_NO_DEPENDS_UNKNOWN:
    ENUMS[field] = ("yes", "no", "depends", "unknown")
for field in ("waste_water_disposal", "grey_water_disposal"):
    ENUMS[field] = ("yes", "no", "unknown")


@dataclass(frozen=True)
class VenueField:
    name: str
    value_type: str
    section: str
    required: bool = False
    read_only_after_create: bool = False
    enum: tuple[str, ...] = ()

    @property
    def python_type(self) -> type:
        return {"integer": int, "decimal": float, "date": date, "boolean": bool}.get(self.value_type, str)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.name.replace("_", " ").title(),
            "type": self.value_type,
            "section": self.section,
            "required": self.required,
            "read_only_after_create": self.read_only_after_create,
            "enum": list(self.enum),
        }


def _field(name: str) -> VenueField:
    if name in INTEGER_FIELDS:
        value_type = "integer"
    elif name in DECIMAL_FIELDS:
        value_type = "decimal"
    elif name in DATE_FIELDS:
        value_type = "date"
    elif name in BOOLEAN_FIELDS:
        value_type = "boolean"
    elif name in ENUMS:
        value_type = "enum"
    elif name in URL_FIELDS:
        value_type = "url"
    elif name in EMAIL_FIELDS:
        value_type = "email"
    elif name in PHONE_FIELDS:
        value_type = "phone"
    elif name in MULTIVALUE_FIELDS:
        value_type = "multivalue"
    elif name in TEXTAREA_FIELDS:
        value_type = "text"
    else:
        value_type = "string"
    return VenueField(
        name=name,
        value_type=value_type,
        section=FIELD_SECTION[name],
        required=name in {"venue_external_id", "venue_name"},
        read_only_after_create=name == "venue_external_id",
        enum=ENUMS.get(name, ()),
    )


VENUE_FIELDS = tuple(_field(name) for name in VENUE_FIELD_NAMES)
VENUE_FIELD_MAP = {field.name: field for field in VENUE_FIELDS}

CONFIDENCE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def schema_document() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "fields": [field.as_dict() for field in VENUE_FIELDS],
        "sections": list(SECTIONS),
        "confidence": {
            "A": "Confirmed by venue or organiser directly",
            "B": "Official website or document",
            "C": "Reliable secondary source",
            "D": "Estimate or inferred",
            "E": "Unknown or placeholder",
        },
        "research_statuses": list(ENUMS["research_status"]),
    }


assert len(VENUE_FIELD_NAMES) == 111
assert set(VENUE_FIELD_NAMES) == set(FIELD_SECTION)
