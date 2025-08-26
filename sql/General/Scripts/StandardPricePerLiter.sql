WITH standard AS (
	SELECT
		b.name as name,
		COALESCE(b.pre_sale_price, b.price) / b."price-unit-content" as standard_price
	FROM beers b
)
SELECT
	name as name,
	standard_price as standard_price
FROM standard
ORDER BY standard_price ASC;