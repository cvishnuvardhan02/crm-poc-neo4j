from analytics.employee_metrics import get_employee_metrics
from analytics.domain_similarity import get_domain_similarity
from analytics.employee_similarity import get_employee_similarity


if __name__ == "__main__":
    print("\n=== EMPLOYEE METRICS ===")
    for row in get_employee_metrics():
        print(row)

    print("\n=== DOMAIN SIMILARITY ===")
    for row in get_domain_similarity():
        print(row)

    print("\n=== EMPLOYEE SIMILARITY ===")
    for row in get_employee_similarity():
        print(row)
