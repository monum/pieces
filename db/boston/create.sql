CREATE TABLE boston_requests (
        id                      SERIAL PRIMARY KEY NOT NULL,
        service_request_id      text DEFAULT NULL,
        service_name            text DEFAULT NULL,
        service_code            text DEFAULT NULL,
        description             text DEFAULT NULL,
        status                  VARCHAR(10) DEFAULT NULL,
        lat                     double precision DEFAULT NULL,
        lng                     double precision DEFAULT NULL,
        neighborhood            text DEFAULT NULL,
        requested_datetime      timestamp DEFAULT NULL,
        updated_datetime        timestamp DEFAULT NULL,
        address                 text DEFAULT NULL,
        media_url               text DEFAULT NULL,
        channel                 text DEFAULT NULL,
        department              text DEFAULT NULL,
        division                text DEFAULT NULL,
        service_type            text DEFAULT NULL,
        queue                   text DEFAULT NULL,
        category                text DEFAULT NULL
);

CREATE INDEX boston_requested_day_idx ON boston_requests ( DATE(requested_datetime) );
CREATE INDEX boston_updated_day_idx ON boston_requests ( DATE(updated_datetime) );
CREATE INDEX boston_neighborhood_idx ON boston_requests ( neighborhood );
CREATE INDEX boston_request_status_idx ON boston_requests ( status );