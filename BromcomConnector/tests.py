from BromcomConnector import bromcom_connect


def test_get_students_by_id():

    student_dicts = bromcom_connect.BromcomConnector.get_entity_by_ids("Students", "StudentId", [2012, 2122, 2211])

    students = []

    for student_data in student_dicts:
        students.append(bromcom_connect.Student(student_data))

    return students


def test_get_collections_by_id():

    collections = bromcom_connect.BromcomConnector.get_entity_by_ids("BehaviourEventRecords", "StudentId",
                                                                     [5955, 9148, 2163],
                                                                     [("EventName","PraiseExcel")],
                                                                     "EventDate", False)

    if collections:
        for c in collections:
            print(c)
    else:
        print("No results")


c = bromcom_connect.Collection(
    bromcom_connect.BromcomConnector.get_entity_by_ids("Collections", "CollectionID", [89])[0]
)

c.load_behaviours_into_students()
for s in c.get_students():

    print(f"{s.display_name}:")
    for b in s.get_behaviour_events():
        print(f"\t{b}")