-- use standard_price instead of price if needed
-- potentially take rating into account with a utility function 
-- e.g. score = a * price + b * rating
WITH order_price_cte AS (
	SELECT 
		name as name,
		CEIL(10 / "price-unit-content") * price as order_price
	FROM beers
)
SELECT
	*
FROM order_price_cte
ORDER BY order_price