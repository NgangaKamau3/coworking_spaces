create database cwspaces;
use cwspaces;

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;


CREATE TABLE lu_user_type (
    user_type_code      TEXT PRIMARY KEY,
    user_type_desc      TEXT NOT NULL
);

CREATE TABLE lu_venue_type (
    venue_type_code     TEXT PRIMARY KEY,
    venue_type_desc     TEXT NOT NULL
);

CREATE TABLE lu_payment_method (
    payment_method_code TEXT PRIMARY KEY,
    payment_method_desc TEXT NOT NULL
);

CREATE TABLE lu_booking_status (
    booking_status_code TEXT PRIMARY KEY,
    booking_status_desc TEXT NOT NULL
);

CREATE TABLE lu_payment_status (
    payment_status_code TEXT PRIMARY KEY,
    payment_status_desc TEXT NOT NULL
);

CREATE TABLE lu_account_status (
    account_status_code TEXT PRIMARY KEY,
    account_status_desc TEXT NOT NULL
);

CREATE TABLE lu_subscription_plan (
    subscription_plan_code TEXT PRIMARY KEY,
    subscription_plan_desc TEXT NOT NULL
);

CREATE TABLE lu_billing_cycle (
    billing_cycle_code  TEXT PRIMARY KEY,
    billing_cycle_desc  TEXT NOT NULL
);

CREATE TABLE lu_space_type (
    space_type_code TEXT PRIMARY KEY,
    space_type_desc TEXT NOT NULL
);

/* ============================================================
   Identity / Users
   ============================================================ */

CREATE TABLE app_user (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name           TEXT        NOT NULL,
    email               CITEXT      NOT NULL UNIQUE,
    phone_number        TEXT,
    password_hash       TEXT        NOT NULL,
    user_type_code      TEXT        NOT NULL REFERENCES lu_user_type(user_type_code),
    preferred_language  TEXT,
    profile_picture_url TEXT,
    last_login          TIMESTAMPTZ,
    account_status_code TEXT        NOT NULL REFERENCES lu_account_status(account_status_code),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_app_user_status ON app_user(account_status_code);

/* ============================================================
   Corporate Accounts
   ============================================================ */

CREATE TABLE company (
    company_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name            TEXT        NOT NULL,
    subscription_plan_code  TEXT        REFERENCES lu_subscription_plan(subscription_plan_code),
    billing_cycle_code      TEXT        REFERENCES lu_billing_cycle(billing_cycle_code),
    active_flag             BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id      UUID        REFERENCES app_user(user_id)
);

/* ============================================================
   Venues
   ============================================================ */

CREATE TABLE venue (
    venue_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_name          TEXT        NOT NULL,
    venue_type_code     TEXT        NOT NULL REFERENCES lu_venue_type(venue_type_code),
    owner_user_id       UUID        REFERENCES app_user(user_id),
    address             TEXT        NOT NULL,
    city                TEXT        NOT NULL,
    country_code        CHAR(2)     NOT NULL,
    latitude            NUMERIC(9,6) NOT NULL,
    longitude           NUMERIC(9,6) NOT NULL,
    wifi_speed_mbps     INTEGER,
    amenities_json      JSONB,
    operating_hours_json JSONB     NOT NULL,
    pricing_model       TEXT        NOT NULL,
    active_flag         BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_venue_type ON venue(venue_type_code);
CREATE INDEX idx_venue_geo  ON venue(latitude, longitude);
CREATE INDEX idx_venue_active ON venue(active_flag);
CREATE INDEX idx_venue_location_gist ON venue USING GIST (ll_to_earth(latitude, longitude));

/* ============================================================
   Spaces
   ============================================================ */

CREATE TABLE space (
    space_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id            UUID        NOT NULL REFERENCES venue(venue_id) ON DELETE CASCADE,
    space_name          TEXT        NOT NULL,
    capacity            INTEGER     NOT NULL CHECK (capacity >= 1),
    hourly_rate         NUMERIC(10,2),
    daily_rate          NUMERIC(10,2),
    availability_status TEXT        NOT NULL DEFAULT 'Available',
    space_amenities_json JSONB,
    space_type_code     TEXT        REFERENCES lu_space_type(space_type_code),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_space_venue ON space(venue_id);

/* ============================================================
   Bookings
   ============================================================ */

CREATE TABLE booking (
    booking_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES app_user(user_id),
    venue_id            UUID        NOT NULL REFERENCES venue(venue_id),
    space_id            UUID        REFERENCES space(space_id),
    booking_start_time  TIMESTAMPTZ NOT NULL,
    booking_end_time    TIMESTAMPTZ NOT NULL,
    booking_status_code TEXT        NOT NULL REFERENCES lu_booking_status(booking_status_code),
    total_price         NUMERIC(12,2) NOT NULL DEFAULT 0,
    payment_status_code TEXT        NOT NULL REFERENCES lu_payment_status(payment_status_code),
    company_id          UUID        REFERENCES company(company_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (booking_end_time > booking_start_time)
);

CREATE INDEX idx_booking_user    ON booking(user_id);
CREATE INDEX idx_booking_venue   ON booking(venue_id, booking_start_time);
CREATE INDEX idx_booking_space   ON booking(space_id);
CREATE INDEX idx_booking_company ON booking(company_id);

/* ============================================================
   Booking Participants
   ============================================================ */

CREATE TABLE booking_participant (
    booking_participant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id             UUID NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
    user_id                UUID REFERENCES app_user(user_id),
    guest_email            TEXT,
    invited_flag           BOOLEAN DEFAULT FALSE,
    checked_in_flag        BOOLEAN DEFAULT FALSE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_booking_participant_booking ON booking_participant(booking_id);

/* ============================================================
   Payments
   ============================================================ */

CREATE TABLE payment (
    payment_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id          UUID        NOT NULL REFERENCES booking(booking_id) ON DELETE CASCADE,
    amount              NUMERIC(12,2) NOT NULL,
    currency            CHAR(3)     NOT NULL,
    payment_method_code TEXT        NOT NULL REFERENCES lu_payment_method(payment_method_code),
    transaction_ref     TEXT,
    payment_timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_code         TEXT        NOT NULL REFERENCES lu_payment_status(payment_status_code),
    gateway_payload     JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_booking ON payment(booking_id);

/* ============================================================
   Payment Audit Log
   ============================================================ */

CREATE TABLE payment_audit_log (
    audit_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id         UUID NOT NULL REFERENCES payment(payment_id) ON DELETE CASCADE,
    action_type        TEXT NOT NULL CHECK (action_type IN ('CAPTURED', 'REFUNDED', 'FAILED')),
    performed_by_user  UUID REFERENCES app_user(user_id),
    amount             NUMERIC(12,2) NOT NULL,
    reason             TEXT,
    performed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    snapshot_json      JSONB
);

CREATE INDEX idx_payment_audit_payment ON payment_audit_log(payment_id);

/* ============================================================
   Invoices / Billing
   ============================================================ */

CREATE TABLE invoice (
    invoice_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID        NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    invoice_period_start DATE       NOT NULL,
    invoice_period_end   DATE       NOT NULL,
    currency            CHAR(3)     NOT NULL,
    subtotal_amount     NUMERIC(12,2) NOT NULL,
    tax_amount          NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_amount        NUMERIC(12,2) NOT NULL,
    invoice_status      TEXT        NOT NULL DEFAULT 'Draft',
    issued_date         DATE,
    due_date            DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE invoice_booking_map (
    invoice_id  UUID REFERENCES invoice(invoice_id) ON DELETE CASCADE,
    booking_id  UUID REFERENCES booking(booking_id) ON DELETE CASCADE,
    PRIMARY KEY (invoice_id, booking_id)
);

/* ============================================================
   User Activity Log
   ============================================================ */

CREATE TABLE user_activity_log (
    activity_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    activity_type   TEXT NOT NULL,
    activity_desc   TEXT,
    related_entity  UUID,
    entity_type     TEXT,
    ip_address      INET,
    user_agent      TEXT,
    activity_time   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_activity_user ON user_activity_log(user_id);

/* ============================================================
   Seed Reference Data
   ============================================================ */

INSERT INTO lu_user_type VALUES
    ('Individual','Public / freelancer user'),
    ('CorporateAdmin','Corporate tenant admin'),
    ('CorporateUser','Corporate employee'),
    ('PartnerAdmin','Venue/partner admin')
ON CONFLICT DO NOTHING;

INSERT INTO lu_venue_type VALUES
    ('CoffeeShop','Coffee shop workspace'),
    ('Hotel','Hotel lobby/meeting workspace'),
    ('CoworkingHub','Dedicated coworking facility')
ON CONFLICT DO NOTHING;

INSERT INTO lu_payment_method VALUES
    ('Card','Credit/Debit Card'),
    ('Mpesa','Mobile Money (Mpesa)'),
    ('PayPal','PayPal'),
    ('Wallet','Internal Wallet')
ON CONFLICT DO NOTHING;

INSERT INTO lu_booking_status VALUES
    ('Pending','Awaiting confirmation'),
    ('Confirmed','Confirmed'),
    ('Cancelled','Cancelled'),
    ('Completed','Completed')
ON CONFLICT DO NOTHING;

INSERT INTO lu_payment_status VALUES
    ('Pending','Awaiting payment'),
    ('Paid','Payment completed'),
    ('Failed','Payment failed'),
    ('Refunded','Payment refunded')
ON CONFLICT DO NOTHING;

INSERT INTO lu_account_status VALUES
    ('Active','Active account'),
    ('Suspended','Suspended account'),
    ('Deleted','Deleted account')
ON CONFLICT DO NOTHING;

INSERT INTO lu_subscription_plan VALUES
    ('Basic','Basic subscription'),
    ('Premium','Premium subscription'),
    ('Enterprise','Enterprise subscription')
ON CONFLICT DO NOTHING;

INSERT INTO lu_billing_cycle VALUES
    ('Monthly','Billed monthly'),
    ('Quarterly','Billed quarterly'),
    ('Annual','Billed annually')
ON CONFLICT DO NOTHING;

INSERT INTO lu_space_type VALUES
    ('SharedDesk','Shared desk or hotdesk'),
    ('PrivateRoom','Private room or office'),
    ('Boardroom','Boardroom or meeting room')
ON CONFLICT DO NOTHING;
