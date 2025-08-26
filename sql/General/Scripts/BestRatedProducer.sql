SELECT 
	producer as producer, 
	AVG(rating) as avg_rating
FROM beers
GROUP BY producer
ORDER BY avg_rating DESC;

