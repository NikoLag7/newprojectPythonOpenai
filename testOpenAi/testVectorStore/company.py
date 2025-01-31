from .models import *
class CompanyClass():


    def get_company(self, query, type="default"):
        company = None
        try:
            if type == "default":
                company = Company.objects.get(id_company=query)
            elif type == "name":
                company = Company.objects.get(company_name=query)
        except Exception as e:
            if "get() returned more than one Company" in str(e):
                return "ERROR BY COMPANY DUPLICATED"
        return company

    def create_company(self, id_assistant, id_vector_store, company_name):
        company_new = Company(id_assistant=id_assistant, id_vector_store=id_vector_store, company_name=company_name)
        company_new.save()
        return company_new