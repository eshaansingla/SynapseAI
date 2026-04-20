// SANCHAALAN SAATHI - Supercharged Urban Flood Demo (MERGE-safe, idempotent)
// High scale numbers for impressive hackathon demo

// ── 1. LOCATIONS ─────────────────────────────────────────────────────────────
MERGE (l1:Location {id: 'l_dharavi'}) ON CREATE SET l1.name='Dharavi, Mumbai', l1.ward='Ward 12', l1.lat=19.0530, l1.lng=72.8543
MERGE (l2:Location {id: 'l_kurla'}) ON CREATE SET l2.name='Kurla East, Mumbai', l2.ward='Ward 17', l2.lat=19.0728, l2.lng=72.8826
MERGE (l3:Location {id: 'l_bandra'}) ON CREATE SET l3.name='Bandra West, Mumbai', l3.ward='Ward 22', l3.lat=19.0596, l3.lng=72.8295

// ── 2. SKILLS ────────────────────────────────────────────────────────────────
MERGE (s_med:Skill {name: 'medical_aid'}) ON CREATE SET s_med.category='medical'
MERGE (s_res:Skill {name: 'search_rescue'}) ON CREATE SET s_res.category='technical'
MERGE (s_log:Skill {name: 'logistics'}) ON CREATE SET s_log.category='logistics'
MERGE (s_wat:Skill {name: 'water_purification'}) ON CREATE SET s_wat.category='technical'
MERGE (s_str:Skill {name: 'structural_assessment'}) ON CREATE SET s_str.category='construction'
MERGE (s_cmm:Skill {name: 'community_outreach'}) ON CREATE SET s_cmm.category='education'

// ── 3. NEEDS (Causal chains) ─────────────────────────────────────────────────
MERGE (n1:Need {id: 'n_flood_main'}) ON CREATE SET n1.type='infrastructure', n1.sub_type='flash_flood', n1.description='Severe flooding rendering 15,000 homeless. 6ft water logging.', n1.urgency_score=1.0, n1.population_affected=15000, n1.status='PENDING', n1.reported_at=datetime()
MERGE (n2:Need {id: 'n_road_block'}) ON CREATE SET n2.type='infrastructure', n2.sub_type='road_blockage', n2.description='Massive landslide blocking all major logistics routes to Dharavi.', n2.urgency_score=0.95, n2.population_affected=25000, n2.status='PENDING', n2.reported_at=datetime()
MERGE (n3:Need {id: 'n_supply_chain'}) ON CREATE SET n3.type='food', n3.sub_type='supply_disruption', n3.description='Supply chains completely disrupted, food running out fast.', n3.urgency_score=0.88, n3.population_affected=10500, n3.status='PENDING', n3.reported_at=datetime()
MERGE (n4:Need {id: 'n_food_acute'}) ON CREATE SET n4.type='food', n4.sub_type='acute_shortage', n4.description='Acute food shortage affecting infants and elderly.', n4.urgency_score=0.98, n4.population_affected=850, n4.status='PENDING', n4.reported_at=datetime()
MERGE (n5:Need {id: 'n_structural'}) ON CREATE SET n5.type='shelter', n5.sub_type='structural_damage', n5.description='150 homes collapsed. Thousands sleeping in the open monsoon.', n5.urgency_score=0.90, n5.population_affected=1800, n5.status='PENDING', n5.reported_at=datetime()
MERGE (n6:Need {id: 'n_shelter_crisis'}) ON CREATE SET n6.type='shelter', n6.sub_type='displacement', n6.description='5,000 displaced people requiring mega-camp setup.', n6.urgency_score=0.92, n6.population_affected=5000, n6.status='CLAIMED', n6.reported_at=datetime()
MERGE (n7:Need {id: 'n_water_contam'}) ON CREATE SET n7.type='water_sanitation', n7.sub_type='contamination', n7.description='Sewer lines burst, massive drinking water contamination.', n7.urgency_score=0.93, n7.population_affected=22000, n7.status='PENDING', n7.reported_at=datetime()
MERGE (n8:Need {id: 'n_medical_emerg'}) ON CREATE SET n8.type='medical', n8.sub_type='waterborne_disease', n8.description='Outbreak of cholera and dengue in relief camps.', n8.urgency_score=1.0, n8.population_affected=1200, n8.status='PENDING', n8.reported_at=datetime()
MERGE (n9:Need {id: 'n_rescue_ops'}) ON CREATE SET n9.type='safety', n9.sub_type='stranded_persons', n9.description='150 citizens stranded on building rooftops awaiting airlift.', n9.urgency_score=1.0, n9.population_affected=150, n9.status='VERIFIED', n9.reported_at=datetime()
MERGE (n10:Need {id: 'n_power_out'}) ON CREATE SET n10.type='infrastructure', n10.sub_type='power_outage', n10.description='Major grid failure affecting 15 wards. Rescue operations impaired.', n9.urgency_score=0.85, n10.population_affected=140000, n10.status='PENDING', n10.reported_at=datetime()

// ── 4. LOCATION EDGES ────────────────────────────────────────────────────────
MERGE (n1)-[:LOCATED_IN]->(l1)
MERGE (n2)-[:LOCATED_IN]->(l1)
MERGE (n3)-[:LOCATED_IN]->(l1)
MERGE (n4)-[:LOCATED_IN]->(l1)
MERGE (n5)-[:LOCATED_IN]->(l2)
MERGE (n6)-[:LOCATED_IN]->(l1)
MERGE (n7)-[:LOCATED_IN]->(l2)
MERGE (n8)-[:LOCATED_IN]->(l2)
MERGE (n9)-[:LOCATED_IN]->(l3)
MERGE (n10)-[:LOCATED_IN]->(l2)

// ── 5. CAUSAL CHAINS ─────────────────────────────────────────────────────────
MERGE (n1)-[:CAUSED_BY]->(n2)
MERGE (n2)-[:CAUSED_BY]->(n3)
MERGE (n3)-[:CAUSED_BY]->(n4)
MERGE (n1)-[:CAUSED_BY]->(n5)
MERGE (n5)-[:CAUSED_BY]->(n6)
MERGE (n1)-[:CAUSED_BY]->(n7)
MERGE (n7)-[:CAUSED_BY]->(n8)

// ── 6. SKILL REQUIREMENTS ────────────────────────────────────────────────────
MERGE (n4)-[:REQUIRES_SKILL]->(s_log)
MERGE (n5)-[:REQUIRES_SKILL]->(s_str)
MERGE (n6)-[:REQUIRES_SKILL]->(s_log)
MERGE (n6)-[:REQUIRES_SKILL]->(s_cmm)
MERGE (n7)-[:REQUIRES_SKILL]->(s_wat)
MERGE (n8)-[:REQUIRES_SKILL]->(s_med)
MERGE (n9)-[:REQUIRES_SKILL]->(s_res)
MERGE (n3)-[:REQUIRES_SKILL]->(s_log)

// ── 7. VOLUNTEERS (High Stats / CamelCase) ───────────────────────────────────
MERGE (v1:Volunteer {id: 'v_amit'}) ON CREATE SET v1.name='Amit Kumar', v1.phone='+919999999991', v1.availabilityStatus='ACTIVE', v1.reputationScore=98, v1.totalXP=6500, v1.totalTasksCompleted=85, v1.currentActiveTasks=0, v1.lat=19.0540, v1.lng=72.8550
MERGE (v2:Volunteer {id: 'v_priya'}) ON CREATE SET v2.name='Priya Sharma', v2.phone='+919999999992', v2.availabilityStatus='ACTIVE', v2.reputationScore=95, v2.totalXP=4800, v2.totalTasksCompleted=52, v2.currentActiveTasks=0, v2.lat=19.0720, v2.lng=72.8830
MERGE (v3:Volunteer {id: 'v_rahul'}) ON CREATE SET v3.name='Rahul Singh', v3.phone='+919999999993', v3.availabilityStatus='ACTIVE', v3.reputationScore=100, v3.totalXP=9200, v3.totalTasksCompleted=120, v3.currentActiveTasks=0, v3.lat=19.0590, v3.lng=72.8300
MERGE (v4:Volunteer {id: 'v_meera'}) ON CREATE SET v4.name='Meera Patel', v4.phone='+919999999994', v4.availabilityStatus='ACTIVE', v4.reputationScore=92, v4.totalXP=3400, v4.totalTasksCompleted=35, v4.currentActiveTasks=0, v4.lat=19.0535, v4.lng=72.8548
MERGE (v5:Volunteer {id: 'v_arjun'}) ON CREATE SET v5.name='Arjun Nair', v5.phone='+919999999995', v5.availabilityStatus='ACTIVE', v5.reputationScore=96, v5.totalXP=7100, v5.totalTasksCompleted=91, v5.currentActiveTasks=0, v5.lat=19.0730, v5.lng=72.8820
MERGE (v6:Volunteer {id: 'v_sunita'}) ON CREATE SET v6.name='Sunita Devi', v6.phone='+919999999996', v6.availabilityStatus='ACTIVE', v6.reputationScore=85, v6.totalXP=2600, v6.totalTasksCompleted=28, v6.currentActiveTasks=0, v6.lat=19.0600, v6.lng=72.8290
MERGE (v7:Volunteer {id: 'v_kiran'}) ON CREATE SET v7.name='Kiran Bose', v7.phone='+919999999997', v7.availabilityStatus='BUSY', v7.reputationScore=89, v7.totalXP=4200, v7.totalTasksCompleted=44, v7.currentActiveTasks=1, v7.lat=19.0525, v7.lng=72.8540
MERGE (v8:Volunteer {id: 'v_dev'}) ON CREATE SET v8.name='Dev Menon', v8.phone='+919999999998', v8.availabilityStatus='ACTIVE', v8.reputationScore=80, v8.totalXP=1850, v8.totalTasksCompleted=19, v8.currentActiveTasks=0, v8.lat=19.0720, v8.lng=72.8840

// ── 8. VOLUNTEER LOCATIONS ───────────────────────────────────────────────────
MERGE (v1)-[:LOCATED_IN]->(l1)
MERGE (v2)-[:LOCATED_IN]->(l2)
MERGE (v3)-[:LOCATED_IN]->(l3)
MERGE (v4)-[:LOCATED_IN]->(l1)
MERGE (v5)-[:LOCATED_IN]->(l2)
MERGE (v6)-[:LOCATED_IN]->(l3)
MERGE (v7)-[:LOCATED_IN]->(l1)
MERGE (v8)-[:LOCATED_IN]->(l2)

// ── 9. VOLUNTEER SKILLS ──────────────────────────────────────────────────────
MERGE (v1)-[:HAS_SKILL]->(s_med)
MERGE (v1)-[:HAS_SKILL]->(s_res)
MERGE (v2)-[:HAS_SKILL]->(s_wat)
MERGE (v2)-[:HAS_SKILL]->(s_log)
MERGE (v3)-[:HAS_SKILL]->(s_log)
MERGE (v3)-[:HAS_SKILL]->(s_cmm)
MERGE (v4)-[:HAS_SKILL]->(s_med)
MERGE (v5)-[:HAS_SKILL]->(s_res)
MERGE (v5)-[:HAS_SKILL]->(s_str)
MERGE (v6)-[:HAS_SKILL]->(s_cmm)
MERGE (v6)-[:HAS_SKILL]->(s_log)
MERGE (v7)-[:HAS_SKILL]->(s_med)
MERGE (v7)-[:HAS_SKILL]->(s_wat)
MERGE (v8)-[:HAS_SKILL]->(s_str)
MERGE (v8)-[:HAS_SKILL]->(s_log)
