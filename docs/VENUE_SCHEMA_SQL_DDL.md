# Venue Schema SQL DDL

This is implementation guidance for Codex. It may be adapted for SQLAlchemy/Alembic.

```sql
CREATE TABLE venues (
    id INTEGER PRIMARY KEY,
    venue_external_id TEXT NOT NULL UNIQUE,
    venue_name TEXT NOT NULL,
    venue_slug TEXT,
    venue_category_primary TEXT,
    venue_categories TEXT,
    alternative_names TEXT,
    description TEXT,

    street_address TEXT,
    address_line_2 TEXT,
    postcode TEXT,
    town TEXT NOT NULL,
    municipality TEXT NOT NULL,
    province TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'Netherlands',

    latitude REAL,
    longitude REAL,
    geocode_precision TEXT,
    geocode_source TEXT,
    google_maps_url TEXT,
    openstreetmap_url TEXT,
    website_url TEXT,

    general_email TEXT,
    general_phone TEXT,
    booking_email TEXT,
    booking_phone TEXT,
    manager_name TEXT,
    manager_email TEXT,
    manager_phone TEXT,

    indoor_outdoor TEXT,
    covered_available TEXT,
    surface_types TEXT,
    site_area_notes TEXT,
    number_of_entrances INTEGER,
    number_of_exits INTEGER,
    fenced TEXT,
    lighting_available TEXT,
    security_cameras TEXT,

    vendor_entrance_notes TEXT,
    loading_area_notes TEXT,
    vehicle_access TEXT,
    trailer_access TEXT,
    height_restrictions TEXT,
    weight_restrictions TEXT,
    setup_access_notes TEXT,

    parking_available TEXT,
    parking_capacity_notes TEXT,
    vendor_parking_notes TEXT,
    overnight_parking_allowed TEXT,
    camping_allowed TEXT,
    public_transport_notes TEXT,
    nearest_train_station TEXT,
    nearest_bus_stop TEXT,
    bicycle_parking_available TEXT,

    electricity_available TEXT,
    electricity_connection_notes TEXT,
    electricity_connection_count INTEGER,
    max_electrical_load TEXT,
    three_phase_available TEXT,
    water_available TEXT,
    water_connection_notes TEXT,
    waste_water_disposal TEXT,
    grey_water_disposal TEXT,
    waste_disposal TEXT,
    recycling_available TEXT,
    toilets_available TEXT,
    accessible_toilets TEXT,
    showers_available TEXT,
    wifi_available TEXT,
    mobile_signal_notes TEXT,

    lpg_allowed TEXT,
    generator_allowed TEXT,
    fire_safety_notes TEXT,

    food_vendor_suitability TEXT,
    food_vendors_permitted TEXT,
    typical_pitch_width_m REAL,
    typical_pitch_depth_m REAL,
    typical_pitch_notes TEXT,
    queue_space_notes TEXT,
    seating_nearby TEXT,
    power_reliability_notes TEXT,
    water_proximity_notes TEXT,

    cleaning_fee_policy TEXT,
    deposit_policy TEXT,
    parking_fee_policy TEXT,
    utility_pricing_policy TEXT,

    wheelchair_accessible TEXT,
    accessibility_notes TEXT,

    wind_exposure TEXT,
    shade_availability TEXT,
    drainage_quality TEXT,
    flood_risk TEXT,
    sun_exposure_notes TEXT,
    weather_exposure_notes TEXT,

    site_map_url TEXT,
    vendor_map_url TEXT,
    utility_map_url TEXT,
    parking_map_url TEXT,
    emergency_plan_url TEXT,
    fire_regulations_url TEXT,
    food_regulations_url TEXT,
    photo_gallery_url TEXT,

    source_url_primary TEXT,
    source_url_secondary TEXT,
    source_title_primary TEXT,
    last_researched_at TEXT,
    last_verified_at TEXT,
    research_status TEXT NOT NULL DEFAULT 'discovered',
    confidence_rating TEXT NOT NULL DEFAULT 'D',
    data_owner_notes TEXT,
    internal_notes TEXT,
    active INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_venues_name ON venues(venue_name);
CREATE INDEX idx_venues_town ON venues(town);
CREATE INDEX idx_venues_municipality ON venues(municipality);
CREATE INDEX idx_venues_category ON venues(venue_category_primary);
CREATE INDEX idx_venues_research_status ON venues(research_status);
CREATE INDEX idx_venues_confidence ON venues(confidence_rating);
```

Related tables:

```sql
CREATE TABLE venue_contacts (
    id INTEGER PRIMARY KEY,
    contact_external_id TEXT NOT NULL UNIQUE,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    contact_type TEXT,
    name TEXT,
    role_title TEXT,
    organization TEXT,
    email TEXT,
    phone TEXT,
    mobile TEXT,
    website_url TEXT,
    notes TEXT,
    source_url TEXT,
    last_verified_at TEXT,
    confidence_rating TEXT DEFAULT 'D',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE venue_documents (
    id INTEGER PRIMARY KEY,
    document_external_id TEXT NOT NULL UNIQUE,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    local_path TEXT,
    description TEXT,
    source_url TEXT,
    retrieved_at TEXT,
    last_verified_at TEXT,
    confidence_rating TEXT DEFAULT 'D',
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE venue_aliases (
    id INTEGER PRIMARY KEY,
    alias_external_id TEXT NOT NULL UNIQUE,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    alias_type TEXT,
    source_url TEXT,
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 1
);
```
