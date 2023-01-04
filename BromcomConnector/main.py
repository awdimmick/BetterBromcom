from bromcom_connect import BromcomConnector as bc

# s = bc.get_student_by_name_tutorgroup('Olti', 'Krasniqi', '9W')
# print(f"{s.display_name} - {s.tutor_group}")
# for b in s.behaviour_events:
#     print(b)
# print(f"Net total: {s.behaviour_net_total}, Positive total: {s.behaviour_positive_total}, Negative total: {s.behaviour_negative_total}")

c = bc.get_collection_by_description("9W")
c.load_behaviour_events_for_students()
for s in c.students:
    print(c.students[s].display_name)
    for b in c.students[s].behaviour_events:
        print(f"\t{b}")