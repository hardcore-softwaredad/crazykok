# Venue Field Dictionary

## Identifier Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| venue_external_id | string | yes | Stable import/export key. Do not change casually. |
| venue_name | string | yes | Official or most recognizable venue name. |
| venue_slug | string | no | URL/import friendly slug. |
| alternative_names | text | no | Semicolon-separated aliases if using flat CSV. |
| active | boolean | yes | Use false for deprecated/merged venues. |

## Classification

| Field | Type | Notes |
|---|---|---|
| venue_category_primary | enum | Main venue category. |
| venue_categories | text | Semicolon-separated list for CSV import. |
| description | text | Human-readable description. |

Suggested categories:

- town_square
- market_square
- fairground
- sports_complex
- stadium
- event_hall
- museum
- attraction
- park
- castle
- farm
- campground
- shopping_centre
- industrial_site
- school
- university
- harbour
- airport
- other

## Address and Geocoding

| Field | Type | Notes |
|---|---|---|
| street_address | string | Street and number where known. |
| postcode | string | Dutch postcode format when available. |
| town | string | Town/village. |
| municipality | string | Gemeente. |
| province | string | Usually Drenthe initially. |
| country | string | Netherlands initially. |
| latitude | decimal | WGS84. |
| longitude | decimal | WGS84. |
| geocode_precision | enum | exact, entrance, venue_centroid, street, town_or_area, unknown. |
| geocode_source | enum | official, openstreetmap, google_maps, manual, inferred, unknown. |
| google_maps_url | url | Plain URL. |
| openstreetmap_url | url | Plain URL. |

## Access and Logistics

| Field | Type | Notes |
|---|---|---|
| vendor_entrance_notes | text | Where vendors enter. |
| loading_area_notes | text | Loading/unloading details. |
| vehicle_access | enum | yes, no, restricted, unknown. |
| trailer_access | enum | yes, no, restricted, unknown. |
| height_restrictions | text | Low bridges, gates, indoor height, etc. |
| weight_restrictions | text | Vehicle/site restrictions. |
| setup_access_notes | text | Time windows or special restrictions. |
| parking_available | enum | yes, no, limited, unknown. |
| vendor_parking_notes | text | Vendor-specific parking details. |
| overnight_parking_allowed | enum | yes, no, with_permission, unknown. |
| camping_allowed | enum | yes, no, with_permission, unknown. |

## Utilities

| Field | Type | Notes |
|---|---|---|
| electricity_available | enum | yes, no, limited, unknown. |
| electricity_connection_notes | text | Outlet location, bring cable, etc. |
| electricity_connection_count | integer | If known. |
| max_electrical_load | string | e.g. 230V/16A, 400V/32A. |
| three_phase_available | enum | yes, no, unknown. |
| water_available | enum | yes, no, limited, unknown. |
| waste_water_disposal | enum | yes, no, unknown. |
| grey_water_disposal | enum | yes, no, unknown. |
| waste_disposal | enum | yes, no, limited, unknown. |
| recycling_available | enum | yes, no, unknown. |
| toilets_available | enum | yes, no, unknown. |
| accessible_toilets | enum | yes, no, unknown. |
| showers_available | enum | yes, no, unknown. |
| wifi_available | enum | yes, no, limited, unknown. |

## Vendor Suitability

| Field | Type | Notes |
|---|---|---|
| food_vendor_suitability | enum | excellent, good, fair, poor, unknown. |
| food_vendors_permitted | enum | yes, no, depends, unknown. |
| typical_pitch_width_m | decimal | Static typical value only if venue-level. |
| typical_pitch_depth_m | decimal | Static typical value only if venue-level. |
| typical_pitch_notes | text | Otherwise opportunity-specific. |
| queue_space_notes | text | Customer queue room. |
| seating_nearby | enum | yes, no, limited, unknown. |
| power_reliability_notes | text | Known issues. |
| water_proximity_notes | text | Distance to water point, if known. |

## Weather Exposure

| Field | Type | Notes |
|---|---|---|
| wind_exposure | enum | low, medium, high, unknown. |
| shade_availability | enum | none, limited, moderate, good, unknown. |
| drainage_quality | enum | poor, fair, good, unknown. |
| flood_risk | enum | low, medium, high, unknown. |
| sun_exposure_notes | text | Afternoon sun, south-facing, etc. |
| weather_exposure_notes | text | General weather notes. |

## Research Fields

| Field | Type | Notes |
|---|---|---|
| source_url_primary | url | Main source. |
| source_url_secondary | url | Secondary source. |
| last_researched_at | date | Date researched. |
| last_verified_at | date | Date verified. |
| research_status | enum | discovered, identified, researched, verified, complete, archived. |
| confidence_rating | enum | A, B, C, D, E. |
| data_owner_notes | text | Data quality notes. |
| internal_notes | text | Private notes. |
