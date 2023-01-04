import requests
from BromcomConnector.settings import Settings
from BromcomConnector.model import *


class BromcomAuthError(Exception):
    pass


class BromcomConnector:

    def __init__(self, username, password, bromcom_data_url="https://cloudmis.bromcom.com/Nucleus/OData/"):

        self.__session = requests.Session()
        self.__session.auth = (username, password)
        self.__BromcomODataURL = bromcom_data_url

        try:
            response = self.__session.get(self.__BromcomODataURL)
            if response.status_code != 200:
                raise BromcomAuthError

        except Exception as e:
            print(e)
            raise BromcomAuthError

    def get_entity_by_ids(self, entity_name: str, id_field_name:str, ids: list, filters: list=None, orderby_key=None,orderby_ascending=True):

        MAX_BATCH_SIZE = 20

        ids_queue = ids.copy()

        entity_dicts = []

        while len(ids_queue) > 0:

            query_string = f"{entity_name}?$filter="

            quote = "'"

            if filters is not None:

                for f in filters:

                    query_string += f"({f[0]} eq " \
                                    f"{quote if type(f[0]) == str else ''}" \
                                    f"{f[1]}" \
                                    f"{quote if type(f[0]) == str else ''}) and "

            query_string += "("

            for i in range(MAX_BATCH_SIZE):
                try:
                    query_string += f"{id_field_name} eq " \
                                    f"{quote if type(ids_queue[0]) == str else ''}" \
                                    f"{ids_queue[0]}" \
                                    f"{quote if type(ids_queue[0]) == str else ''} or "
                    del ids_queue[0]

                except IndexError:
                    break

            query_string = query_string[:-4] + ")"

            print(f"DEBUG: Query string: {self.__BromcomODataURL}{query_string}")

            response = self.__session.get(
                self.__BromcomODataURL + query_string
            )

            try:
                entity_dicts = response.json()['value']

                if orderby_key is not None:

                    entity_dicts = sorted(entity_dicts, key=lambda entity: entity[orderby_key])

                    if not orderby_ascending:
                        entity_dicts.reverse()

                return entity_dicts

            except KeyError:
                return None

    def get_student_by_id(self, id:int):

        print(f"LOG: Retrieving student {id}.")

        student_response = self.__session.get(
            self.__BromcomODataURL +
            f"Students?$filter=StudentId eq {id}"
        )

        return Student(student_response.json()['value'][0], self)

    def get_student_by_name_tutorgroup(self, first_name, last_name, tutorgroup):

        print(f"LOG: Retrieving {first_name} {last_name} from {tutorgroup}.")

        response = self.__session.get(
            self.__BromcomODataURL +
            f"Students?$filter=PreferredFirstName eq '{first_name}' and PreferredLastName eq '{last_name}' and TutorGroup eq '{tutorgroup}'"
        )

        return Student(response.json()['value'][0], self)

    def get_students_for_tutor_group(self, tutor_group:str):

        print(f"LOG: Retrieving students for {tutor_group}.")

        students = []

        students_response = self.__session.get(
            self.__BromcomODataURL +
            f"Students?$filter=TutorGroup eq '{tutor_group}'"
        )

        for data in students_response.json()['value']:
            students.append(Student(data, self))

        return students

    def get_students_for_class(self, class_name:str):

        print(f"LOG: Retrieving students for {class_name}.")

        student_ids = []
        students = []

        student_classes = self.__session.get(
            self.__BromcomODataURL +
            f"StudentClasses?$filter=ClassName eq '{class_name}'"
        ).json()['value']

        for sc in student_classes:
            student_ids.append(int(sc['StudentId']))

        while len(student_ids) > 0:
            students_filter_string = ""
            # Multi select maxes out at 20 so need to process in batches
            for i in range(20):
                try:
                    students_filter_string += f"StudentId eq {student_ids[0]} or "
                    del student_ids[0]
                except:
                    pass
            students_filter_string = students_filter_string[:-4]

            students_response_url = self.__BromcomODataURL + "Students?$filter=" + students_filter_string

            student_dicts = self.__session.get(students_response_url).json()['value']

            for student_data in student_dicts:
                students.append(Student(student_data, self))

        return students

    def get_collection_by_id(self, collection_id:int):

        print(f"LOG: Retrieving collection {collection_id}.")

        collection_response = self.__session.get(
            self.__BromcomODataURL +
            f"Collections?$filter=CollectionID eq {collection_id}"
        )

        return Collection(collection_response.json()['value'][0], self)

    def get_collection_by_description(self, description:str):

        print(f"LOG: Retrieving collection {description}.")

        collection_response = self.__session.get(
            self.__BromcomODataURL +
            f"Collections?$filter=CollectionDescription eq '{description}'"
        )

        return Collection(collection_response.json()['value'][0], self)

    def get_main_teacher_for_tutor_group(self, id:int):

        teacher_response = self.__session.get(
            self.__BromcomODataURL +
            f"CollectionExecutives?$filter=CollectionID eq {id} and CollectionRoleTypeDescription eq 'Main Tutor'"
        )

        return teacher_response.json()['value'][-1]['StaffID']

    def get_main_teacher_for_teaching_group(self, id:int):
        teacher_response = self.__session.get(
            self.__BromcomODataURL +
            f"CollectionExecutives?$filter=CollectionID eq {id}"
        )

        ids = []

        for t in teacher_response.json()['value']:
            ids.append(t['StaffID'])

        return ids
