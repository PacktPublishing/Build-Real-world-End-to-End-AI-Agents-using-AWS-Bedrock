CREATE TABLE rental_listings
(
    id             VARCHAR(64)         ENCODE lzo
  , operation      VARCHAR(15)         ENCODE lzo
  , property_type  VARCHAR(20)         ENCODE lzo
  , place_name     VARCHAR(100)        ENCODE lzo
  , country_name   VARCHAR(50)         ENCODE lzo
  , price          DECIMAL(18,2)       ENCODE az64
  , currency       CHAR(3)             ENCODE lzo
  , description    VARCHAR(65535)      ENCODE lzo
  , title          VARCHAR(255)        ENCODE lzo
);

COPY rental_listings
FROM 's3://{bucket-name}/rental_listings.csv'
IAM_ROLE 'arn:aws:iam::127489365181:role/service-role/{Role-name}'
REGION 'us-east-1'
FORMAT AS CSV
FILLRECORD
IGNOREHEADER 1;