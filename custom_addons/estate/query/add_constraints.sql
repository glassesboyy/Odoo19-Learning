-- Script untuk menambahkan constraints secara manual
-- Jalankan di PostgreSQL database Odoo Anda

-- 1. Hapus data yang melanggar constraint (OPSIONAL - jika ingin pertahankan data lain)
DELETE FROM estate_property WHERE expected_price <= 0;
DELETE FROM estate_property WHERE selling_price < 0;
DELETE FROM estate_property_offer WHERE price <= 0;

-- Hapus tag duplikat (keep only first occurrence)
DELETE FROM estate_property_tag a
USING estate_property_tag b
WHERE a.id > b.id AND a.name = b.name;

-- Hapus type duplikat (keep only first occurrence)
DELETE FROM estate_property_type a
USING estate_property_type b
WHERE a.id > b.id AND a.name = b.name;

-- 2. Tambahkan Constraints
-- Property expected_price constraint
ALTER TABLE estate_property 
  DROP CONSTRAINT IF EXISTS estate_property_check_expected_price_positive;
ALTER TABLE estate_property 
  ADD CONSTRAINT estate_property_check_expected_price_positive 
  CHECK(expected_price > 0);

-- Property selling_price constraint
ALTER TABLE estate_property 
  DROP CONSTRAINT IF EXISTS estate_property_check_selling_price_positive;
ALTER TABLE estate_property 
  ADD CONSTRAINT estate_property_check_selling_price_positive 
  CHECK(selling_price >= 0);

-- Offer price constraint
ALTER TABLE estate_property_offer 
  DROP CONSTRAINT IF EXISTS estate_property_offer_check_offer_price_positive;
ALTER TABLE estate_property_offer 
  ADD CONSTRAINT estate_property_offer_check_offer_price_positive 
  CHECK(price > 0);

-- Tag unique name constraint
ALTER TABLE estate_property_tag 
  DROP CONSTRAINT IF EXISTS estate_property_tag_unique_tag_name;
ALTER TABLE estate_property_tag 
  ADD CONSTRAINT estate_property_tag_unique_tag_name 
  UNIQUE(name);

-- Type unique name constraint
ALTER TABLE estate_property_type 
  DROP CONSTRAINT IF EXISTS estate_property_type_unique_type_name;
ALTER TABLE estate_property_type 
  ADD CONSTRAINT estate_property_type_unique_type_name 
  UNIQUE(name);

-- 3. Verify constraints
SELECT 
  conrelid::regclass AS table_name,
  conname AS constraint_name,
  contype AS constraint_type,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid::regclass::text LIKE 'estate_%'
ORDER BY table_name, constraint_name;
