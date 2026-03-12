CREATE USER "IAMR:redshift-bedrock-sr" WITH PASSWORD DISABLE;

GRANT SELECT ON ALL TABLES IN SCHEMA "public" TO "IAMR:redshift-bedrock-sr";

GRANT SELECT ON public.rental_listings TO "IAMR:redshift-bedrock-sr";