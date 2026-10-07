// Employee performance
MATCH (e:Employee)-[:OWNS]->(o:Opportunity)
RETURN e.name AS employee,
       count(o) AS opportunities,
       sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) AS wins,
       round(
         100.0 * sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) / count(o), 2
       ) AS win_rate
ORDER BY win_rate DESC;

// Employee -> Domain performance
MATCH (e:Employee)-[:OWNS]->(o:Opportunity)-[:TARGETS]->(d:Domain)
RETURN e.name AS employee,
       d.name AS domain,
       count(o) AS opportunities,
       sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) AS wins,
       round(
         100.0 * sum(CASE WHEN o.outcome = 'Won' THEN 1 ELSE 0 END) / count(o), 2
       ) AS win_rate
ORDER BY employee, win_rate DESC;

// Domain relationships
MATCH (d1:Domain)<-[:TARGETS]-(o:Opportunity)-[:TARGETS]->(d2:Domain)
WHERE d1.name < d2.name
RETURN d1.name AS domain_1, d2.name AS domain_2, count(*) AS co_occurrence
ORDER BY co_occurrence DESC;

// Open opportunities
MATCH (e:Employee)-[:OWNS]->(o:Opportunity)
WHERE o.stage = 'Open'
RETURN o.id, o.name, e.name, o.domain, o.value
ORDER BY o.value DESC;
