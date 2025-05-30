## VÄRDERA

## Airflow + Django + Superset
> **Branch:** `final_project`

This repository demonstrates the integration of three powerful open-source tools: **Apache Airflow** for workflow orchestration, **Django** as a web backend, and **Apache Superset** for business intelligence and data visualization.

YouTube video tutorial:
https://www.youtube.com/watch?v=CBSuzNml3DQ



---

## Project Structure

- **airflow/**  
  ETL pipeline and ML CI/CD.

- **backups/**  
  Stores backups of PostgreSQL data.

- **ml_development/**  
  A sandbox for machine learning: develop, test, and manage ML models or experiments.

- **real_estate_dash/**  
  The Django web application.

- **shared_data/**  
  A central location for model *.pkl files. 

- **superset/**  
  Contains Superset’s files.

- **superset_home/**  
  Stores Superset configurations.

---
> **Note:** This list may not cover all files and directories. [Browse the full file tree on GitHub.](https://github.com/abbosjonvositov/airflow_django_superset/tree/final_project)


## Getting Started

1. **Clone the repository**
   ```bash
   git clone -b final_project https://github.com/abbosjonvositov/airflow_django_superset.git
   cd airflow_django_superset
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the UIs:**
   - Airflow: http://localhost:8080
   - Django:  http://localhost:8000
   - Superset: http://localhost:8088

4. **Default credentials**
   - Airflow: `admin/admin`
   - Superset: `admin/admin`

---

## Key Technologies

- **Apache Airflow**: Workflow automation and scheduling
- **Django**: Python web framework
- **Apache Superset**: Data analytics and visualization
- **Docker Compose**: Container orchestration for local development

---


## Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Apache Superset Documentation](https://superset.apache.org/docs/)