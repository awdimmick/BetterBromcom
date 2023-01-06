from datetime import datetime

from BromcomConnector import bromcom_connect

class Collection:

    def __init__(self, data, bromcom_connector):

        # All model objects require a reference to a BromcomConnector object in order to access data
        self.__bromcom_connector = bromcom_connector

        self.__id = int(data['CollectionID'])
        self.__name = data['CollectionName']
        self.__description = data['CollectionDescription']
        self.__startDate = data['StartDate']
        self.__endDate = data['EndDate']
        self.__collectionTypeName = data['CollectionTypeName']
        self.__collectionTypeDescription = data['CollectionTypeDescription']
        self.__studentIds = None
        self.__students = None
        self.__behaviourEvents = None
        self.__student_behaviours = None
        self.__main_teacher = None

        """
            If the Collection has a type CLASS then we can also get the students by reference to StudentClasses
            If the Collection has a type TUTORGRP the we can get the students by reference to the Students entity, filtering 
            on Student.TutorGroup = Collection.CollectionDescription
            """
        print(self.main_teacher)

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def type_description(self):
        return self.__collectionTypeDescription

    @property
    def main_teacher(self):

        if self.__main_teacher :
            return self.__main_teacher

        if self.__collectionTypeName == "TUTORGRP":
            main_teacher_ids = [self.__bromcom_connector.get_main_teacher_for_tutor_group(self.__id)]
        else:
            # could be multiple
            main_teacher_ids = self.__bromcom_connector.get_main_teacher_for_teaching_group(self.__id)

        main_teacher_dicts = self.__bromcom_connector.get_entity_by_ids("Staff", "StaffId", main_teacher_ids)

        main_teacher = f"{main_teacher_dicts[0]['PreferredFirstName']} {main_teacher_dicts[0]['PreferredLastName']} ({main_teacher_dicts[0]['StaffCode']})"

        for t in main_teacher_dicts[1:]:
            main_teacher += f", {t['PreferredFirstName']} {t['PreferredLastName']} ({t['StaffCode']})"

        self.__main_teacher = main_teacher

        return self.__main_teacher

    def get_behaviour_events_with_student_ids(self):

        if self.__student_behaviours is None:
            self.__student_behaviours = {}

            student_dicts = self.__bromcom_connector.\
                get_entity_by_ids("Students", "StudentId", self.get_student_ids(), orderby_key="LegalLastName")

            for sd in student_dicts:
                s = bromcom_connect.Student(sd, self.__bromcom_connector)
                self.__student_behaviours[s.id] = [s]

            for b in self.get_behaviour_events():
                self.__student_behaviours[b.student_id].append(b)

        return self.__student_behaviours

    def get_behaviour_events(self):

        if self.__behaviourEvents is None:

            self.__behaviourEvents = []

            behaviour_dicts = self.__bromcom_connector.\
                get_entity_by_ids("BehaviourEventRecords", "StudentId", self.get_student_ids())

            for data in behaviour_dicts:
                self.__behaviourEvents.append(BehaviourEvent(data, self.__bromcom_connector))

        return self.__behaviourEvents

    def get_student_ids(self):

        if self.__studentIds is None:
            self.__studentIds = []
            if self.__collectionTypeName == "TUTORGRP":
                student_id_dicts = self.__bromcom_connector.\
                    get_entity_by_ids("Students", "TutorGroup", [self.__description])
            elif self.__collectionTypeName == "CLASS": # When searching for students from a teaching group, you must supply the ClassName for the filter
                student_id_dicts = self.__bromcom_connector.\
                    get_entity_by_ids("StudentClasses", "ClassName", [self.__name])
            for student_dict in student_id_dicts:
                self.__studentIds.append(student_dict['StudentId'])

        return self.__studentIds

    def get_students(self):

        if self.__students is None:
            if self.__collectionTypeName == 'TUTORGRP':
                self.__students = self.__bromcom_connector.get_students_for_tutor_group(self.name)
            elif self.__collectionTypeName == "CLASS":
                self.__students = self.__bromcom_connector.get_students_for_class(self.name)

        return self.__students

    def load_behaviours_into_students(self):

        for s in self.get_students():
            print(f"LOG: Retrieving behaviours for Student {s.id}.")
            for b in self.get_behaviour_events():

                if b.student_id == s.id:
                    s.add_behaviour_event(b)


class Student:

    def __init__(self, data, bromcom_connector):

        self.__bromcom_connector = bromcom_connector
        self.__id = data['StudentId']
        self.__preferredFirstName = data['PreferredFirstName']
        self.__preferredLastName = data['PreferredLastName']
        self.__legalFirstName = data['LegalFirstName']
        self.__legalLastName = data['LegalLastName']
        self.__middleName = data['MiddleName']
        # self.__dateOfBirth = datetime.utcfromtimestamp(data['DateOfBirth'])
        # self.__dateOfEntry = datetime.fromisoformat(data['DateOfEntry'])
        self.__dateOfBirth = data['DateOfBirth']
        self.__dateOfEntry = data['DateOfEntry']
        self.__eal = data['EAL'] == "Yes"
        self.__fsm = data['FSM'] == "Yes"
        self.__pp = data['PupilPremium'] == "Yes"
        self.__lac = data['LAC'] == "Yes"
        self.__sen = False if data['SENNeed'] == "" else True
        self.__serviceChild = not data['ServiceChildDescription'] == ""
        self.__senProvision = data['Provision']
        self.__house = data['House']
        self.__tutorGroup = data['TutorGroup']
        self.__yearGroup = int(data['YearGroup'])
        self.__behaviourEvents = []

        #self.get_behaviour_events()

    @property
    def id(self):
        return self.__id

    @property
    def first_name(self):
        return self.__preferredFirstName

    @property
    def last_name(self):
        return self.__preferredLastName

    @property
    def middle_name(self):
        return self.__middleName

    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def house(self):
        return self.__house

    @property
    def sen(self):
        return self.__sen

    @property
    def sen_provision(self):
        return self.__senProvision

    @property
    def tilt(self):
        return self.__fsm or self.__serviceChild or self.__pp

    @property
    def year_group(self):
        return self.__yearGroup

    def get_behaviour_events(self):
        if len(self.__behaviourEvents) == 0:
            self.load_behaviour_events()

        return self.__behaviourEvents

    def get_behaviour_net_total(self):
        total = 0

        for b in self.get_behaviour_events():
            total += b.adjustment

        return total

    def get_behaviour_negative_total(self):

        total = 0

        for b in self.get_behaviour_events():
            if b.type == "Negative":
                total += b.adjustment

        return total

    def get_behaviour_positive_total(self):

        total = 0

        for b in self.get_behaviour_events():
            if b.type == "Positive":
                total += b.adjustment

        return total

    @property
    def tutor_group(self):
        return self.__tutorGroup

    def get_tutor(self):
        pass

    def add_behaviour_event(self, behaviour):
        self.__behaviourEvents.append(behaviour)

    def load_behaviour_events(self):
        for behaviour_data in self.__bromcom_connector.get_entity_by_ids(
                "BehaviourEventRecords", "StudentId", [self.__id]
        ):
            self.__behaviourEvents.append(BehaviourEvent(behaviour_data, self.__bromcom_connector))


class BehaviourEvent:

    def __init__(self, data, bromcom_connector):

        self.__bromcom_connector = bromcom_connector

        self.__eventRecordId = data['EventRecordId']
        self.__studentId = int(data['StudentId'])
        self.__eventType = data['EventType']
        self.__eventName = data['EventName']
        self.__eventDescription = data['EventDescription']
        self.__eventDate = data['EventDate']
        self.__adjustment = int(data['Adjustment'])
        self.__comment = data['Comment']
        self.__internalComment = data['InternalComment']
        self.__dayOfWeek = data['DayOfWeek']
        self.__timetablePeriod = data['TimetablePeriod']
        self.__room = data['TimetablePeriod']
        self.__staffCode = data['StaffCode']
        self.__collectionName = data['CollectionName']
        self.__subject = data['Subject']
        self.__department = data['Department']
        self.__student = None

    @property
    def id(self):
        return self.__eventRecordId

    @property
    def student_id(self):
        return self.__studentId

    def get_student(self):
        if self.__student is None:
            self.__student = Student(self.__bromcom_connector.
                                     get_entity_by_ids("Students", "StudentId", [self.__studentId])[0], self.__bromcom_connector)

        return self.__student

    @property
    def name(self):
        return self.__eventName

    @property
    def type(self):
        return self.__eventType

    @property
    def description(self):
        return self.__eventDescription

    @property
    def comment(self):
        return self.__comment

    @property
    def staff_code(self):
        return self.__staffCode

    @property
    def date(self):
        return self.__eventDate

    @property
    def day_of_week(self):
        return self.__dayOfWeek

    @property
    def adjustment(self):
        return self.__adjustment

    @property
    def collection_name(self):
        return self.__collectionName

    @property
    def collection(self):
        return self.__bromcom_connector.get_collection_by_description(self.collection_name)

    @property
    def subject(self):
        return self.__subject

    def __repr__(self):
        return f"{self.type}, {self.adjustment} - {self.description}: {self.comment} ({self.staff_code}, {self.date})"
