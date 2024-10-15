import json
import csv
import zipfile
from io import TextIOWrapper

race_lookup = {
    "1": "American Indian or Alaska Native",
    "2": "Asian",
    "3": "Black or African American",
    "4": "Native Hawaiian or Other Pacific Islander",
    "5": "White",
    "21": "Asian Indian",
    "22": "Chinese",
    "23": "Filipino",
    "24": "Japanese",
    "25": "Korean",
    "26": "Vietnamese",
    "27": "Other Asian",
    "41": "Native Hawaiian",
    "42": "Guamanian or Chamorro",
    "43": "Samoan",
    "44": "Other Pacific Islander"
}
keys = list(race_lookup.keys())

class Applicant:
    def __init__(self, age, race):
        self.age = age
        self.race = set()
        for r in race:
            if r in keys:
                self.race.add(race_lookup[r])
    
    def __repr__(self):
        return f"Applicant({repr(self.age)}, {repr(sorted(self.race))})"
    
    def lower_age(self):
        if("<" in self.age or ">" in self.age):
            return int(self.age[1:])
        return int(self.age.split("-")[0])
    
    def __lt__(self, other):
        return self.lower_age() < other.lower_age()
    


class Loan:
    def helper(self,string:str):
        if string == "NA" or string == "Exempt":
            return -1
        else: return float(string)
    
    def __init__(self, values):
        temp_amt = values["loan_amount"]
        temp_pv = values["property_value"]
        temp_ir = values["interest_rate"]
        self.loan_amount = self.helper(temp_amt)
        self.property_value = self.helper(temp_pv)
        self.interest_rate = self.helper(temp_ir)
        self.applicants = []
        app_race = []
        for i in range(1,6):
            temp = values["applicant_race-"+str(i)]
            if temp != '' and temp in keys:
                app_race.append(temp)
        self.applicants.append(Applicant(values["applicant_age"],app_race))
        
        if values["co-applicant_age"] != "9999":
            co_app_race = []
            for i in range(1,6):
                temp = values["co-applicant_race-"+str(i)]
                if temp != '' and temp in keys:
                    co_app_race.append(temp)
            self.applicants.append(Applicant(values["co-applicant_age"],co_app_race))
            
        
        
    def __str__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"
    
    def __repr__(self):
        return f"<Loan: {self.interest_rate}% on ${self.property_value} with {len(self.applicants)} applicant(s)>"
    
    def yearly_amounts(self, yearly_payment):
        # TODO: assert interest and amount are positive
        interest = self.interest_rate / 100
        assert interest > 0
        assert self.loan_amount > 0
        result = []
        amt = self.loan_amount

        while amt > 0:
            yield amt
            # TODO: add interest rate multiplied by amt to amt
            amt += amt*interest
            # TODO: subtract yearly payment from amt
            amt -= yearly_payment


class Bank:
        
    def __init__(self, bank_name):
        with open('banks.json', 'r') as file:
            banks = json.load(file)
        self.loans = []
        bank = -1
        for i in range(len(banks)):
            if banks[i]["name"] == bank_name:
                bank = i
                self.lei = banks[i]["lei"]
                break
        if i == -1:
            raise ValueError("Bank name not in banks.json")
        
    def load_from_zip(self, path):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            csv_file = zip_ref.namelist()[0]
            with zip_ref.open(csv_file, 'r') as file:
                text_file = TextIOWrapper(file)
                csv_reader = csv.DictReader(text_file)
                
                for row in csv_reader:
                    if row['lei'] == self.lei:
                        self.loans.append(Loan(row))
       
    
    def __getitem__(self, index):
        return self.loans[index]
    
    def __len__(self):
        return len(self.loans)
    
    def average_interest_rate(self):
        total_interest = 0
        total_loans = 0
        
        for loan in self.loans:
            total_interest += loan.interest_rate
            total_loans += 1
        
        if total_loans == 0:
            return 0
        
        return total_interest / total_loans
    
    def num_applicants(self):
        counter = 0
        for i in self.loans:
            counter += len(i.applicants)
        return counter
    
    def ages_dict(self):
        ages = {}
        for loan in self.loans:
            for applicant in loan.applicants:
                age = applicant.age
                if age in ages:
                    ages[age] += 1
                else:
                    ages[age] = 1
        sorted_ages = {key: ages[key] for key in sorted(ages)}
        return sorted_ages
