.mode column
.headers on

ATTACH DATABASE 'Data/home-assistant_v2.db' as ha_db;

CREATE TEMP VIEW local_states AS
  SELECT state_id, entity_id, state, datetime(last_updated,'localtime') as local_updated, datetime(last_changed,'localtime') as local_changed
  FROM ha_db.states
  WHERE entity_id LIKE 'sensor.%\_current\_consumption' ESCAPE '\'
    OR entity_id = 'binary_sensor.fridge_contact'
    OR entity_id = 'binary_sensor.freezer_contact';

CREATE TEMP VIEW offset_view AS
  SELECT *, lead(state,1) over (PARTITION BY entity_id) as next_state, lead(local_updated,1) over (PARTITION BY entity_id) as next_update
  FROM local_states;

-- CREATE TEMP VIEW dates AS
--   SELECT DISTINCT(datetime(local_updated, 'day'))
--   FROM offset_view;
-- 
-- SELECT * FROM dates;

CREATE TEMP VIEW modified_diff AS
  WITH RECURSIVE datelist AS (
    SELECT datetime(min(local_updated), 'start of day') as unique_day
    FROM local_states
    UNION ALL
    SELECT datetime(unique_day, '+1 day')
    FROM datelist
    WHERE datetime(unique_day,'+1 day') < (SELECT max(date(local_updated)) FROM local_states)
  )
  SELECT *, (min(julianday(next_update),julianday(datelist.unique_day,'+1 day')) - max(julianday(local_updated),julianday(datelist.unique_day)))*60*60*24 as duration, date(datelist.unique_day) as day
  FROM offset_view
  JOIN datelist
  WHERE local_updated <= datetime(datelist.unique_day, '+1 day')
    AND next_update > datelist.unique_day;


CREATE TEMP VIEW sensor_day_state AS
  SELECT day, entity_id, state, SUM(duration)/60 as daily_duration_min, count(state) as quantity, strftime('%w',day) as day_of_week
  FROM modified_diff
  WHERE entity_id = 'binary_sensor.fridge_contact'
    OR entity_id = 'binary_sensor.freezer_contact'
  GROUP BY day, entity_id, state;

CREATE TEMP VIEW power_day AS
  SELECT day, entity_id, sum(state*duration)/(3.6*power(10,6)) as 'energy_kwh', sum(state*duration)/1000 as 'energy_kj', sum(state*duration)/(3.6*power(10,6))*.14 as price_per_day, sum(duration)/60 as daily_duration_min, count(state) as quantity, strftime('%w',day) as day_of_week
  FROM modified_diff
  WHERE entity_id LIKE 'sensor.%\_current\_consumption' ESCAPE '\'
  GROUP BY day, entity_id;

.mode csv

.output Data/fridge_freezer_on.csv
SELECT * FROM local_states
WHERE state = "on";

.output Data/fridge_states.csv
SELECT * FROM sensor_day_state;

.output Data/power_usage.csv
SELECT * FROM power_day;
