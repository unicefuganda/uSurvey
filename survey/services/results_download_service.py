from survey.models import LocationTypeDetails, Investigator, Household


class ResultsDownloadService(object):
    def __init__(self, batch):
        self.batch = batch
        self.questions = self.batch.all_questions()

    def set_report_headers(self):
        header = list(LocationTypeDetails.get_ordered_types().exclude(name__iexact="country").values_list('name', flat=True))
        other_headers = ['Household ID', 'Name', 'Age', 'Month of Birth', 'Year of Birth', 'Gender']
        header.extend(other_headers)
        header.extend(self.question_headers())
        return header

    def question_headers(self):
        header = []
        for question in self.questions:
            header.append(question.identifier)
            if question.is_multichoice():
                header.append('')
        return header

    def get_summarised_answers(self):
        data = []
        all_households = Household.objects.filter(survey=self.batch.survey)
        locations = list(set(all_households.values_list('location', flat=True)))
        for location_id in locations:
            households_in_location = all_households.filter(location=location_id)
            household_location = households_in_location[0].location
            location_ancestors = list(household_location.get_ancestors(include_self=True).exclude(type__name__iexact="country").values_list('name', flat=True))
            for household in households_in_location:
                for member in household.all_members():
                    member_gender = 'Male' if member.male else 'Female'
                    answers = location_ancestors
                    answers = answers + [household.household_code, member.surname, str(int(member.get_age())),
                                         str(member.get_month_of_birth()), str(member.get_year_of_birth()),
                                         member_gender]
                    answers = answers + member.answers_for(self.questions)
                    data.append(answers)
        return data

    def generate_report(self):
        data = [self.set_report_headers()]
        data.extend(self.get_summarised_answers())
        return data
