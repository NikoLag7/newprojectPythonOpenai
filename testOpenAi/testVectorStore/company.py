from .models import *
class Company():

    def __init__(self,id_company):
        self.id_company = id_company

    def get_company(self, query):
        company = None
        try:
            line_defense = Company.objects.get(id=query)
        except Exception as e:
            if "get() returned more than one Company" in str(e):
                return "ERROR BY COMPANY DUPLICATED"
        return company

    def create_company(self, id_assistant, id_vectore_store):
        pass