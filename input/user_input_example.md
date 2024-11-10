The **Construction Project Management System** is designed to help construction companies manage and track multiple construction projects and their respective phases. This system allows companies to store information about project owners, project details, various stages of construction, and the materials/resources required for each phase.

This system includes:
1. **Owners**: Individuals or entities that own or finance the construction projects (`owners` table).
2. **Construction Projects**: Details of each project, such as location, type, start and end dates (`projects` table).
3. **Project Phases**: Specific phases within a project, each with its timeline and requirements (`phases` table).
4. **Resources and Materials**: Materials and tools associated with each phase, tracked to manage inventory and budgeting (`resources` table).

With this system, construction companies can track the lifecycle of each project, manage resources effectively, and ensure that all required materials are available for every phase of construction.

---

### **Table Definitions**

#### 1. **Owners**

(`owners` table)
 
| Field Name       | Field Type   | Field Length | Primary Key | Description                                         |
|------------------|--------------|--------------|-------------|-----------------------------------------------------|
| `owner_id`       | INT          | -            | Yes         | Unique identifier for each owner.                   |
| `name`           | VARCHAR      | 100          | No          | Name of the owner or entity financing the project.  |
| `contact_email`  | VARCHAR      | 100          | No          | Email address of the owner for contact purposes.    |
| `phone_number`   | VARCHAR      | 15           | No          | Contact phone number of the owner.                  |
| `address`        | VARCHAR      | 255          | No          | Physical address of the owner.                      |

**Description**: Stores information about the owners or entities that are financing each construction project.

#### 2. **Construction Projects**

(`projects` table)

| Field Name       | Field Type   | Field Length | Primary Key | Description                                            |
|------------------|--------------|--------------|-------------|--------------------------------------------------------|
| `project_id`     | INT          | -            | Yes         | Unique identifier for each project.                    |
| `owner_id`       | INT          | -            | No (FK)     | References the owner financing the project.            |
| `project_name`   | VARCHAR      | 150          | No          | Name of the construction project.                      |
| `location`       | VARCHAR      | 255          | No          | Location where the project is being executed.          |
| `start_date`     | DATE         | -            | No          | Starting date of the project.                          |
| `end_date`       | DATE         | -            | No          | Estimated or actual completion date of the project.    |
| `project_type`   | VARCHAR      | 50           | No          | Type of construction (e.g., residential, commercial).  |

**Description**: Contains details of each construction project, including ownership, location, and duration.

#### 3. **Project Phases**

(`phases` table)

| Field Name       | Field Type   | Field Length | Primary Key | Description                                            |
|------------------|--------------|--------------|-------------|--------------------------------------------------------|
| `phase_id`       | INT          | -            | Yes         | Unique identifier for each project phase.              |
| `project_id`     | INT          | -            | No (FK)     | References the associated project.                     |
| `phase_name`     | VARCHAR      | 100          | No          | Name or description of the project phase.              |
| `start_date`     | DATE         | -            | No          | Starting date of the phase.                            |
| `end_date`       | DATE         | -            | No          | Completion date of the phase.                          |
| `phase_status`   | ENUM         | -            | No          | Status of the phase (e.g., pending, in-progress, complete).|

**Description**: Tracks specific phases of each construction project, such as foundation, framing, plumbing, and electrical phases.

#### 4. **Resources and Materials**

(`resources` table)

| Field Name       | Field Type   | Field Length | Primary Key | Description                                            |
|------------------|--------------|--------------|-------------|--------------------------------------------------------|
| `material_id`    | INT          | -            | Yes         | Unique identifier for each material.                   |
| `material_name`  | VARCHAR      | 100          | No          | Name or description of the material or resource.       |
| `unit_cost`      | DECIMAL(10,2)| -            | No          | Cost per unit of the material.                         |
| `quantity`       | INT          | -            | No          | Quantity available in stock.                           |
| `supplier_name`  | VARCHAR      | 100          | No          | Supplier providing the material.                       |

**Description**: Stores details about the resources and materials required for the construction projects, including inventory levels and cost per unit.

#### 5. **Phase Materials**

| Field Name       | Field Type   | Field Length | Primary Key | Description                                            |
|------------------|--------------|--------------|-------------|--------------------------------------------------------|
| `phase_material_id` | INT      | -            | Yes         | Unique identifier for each phase material entry.       |
| `phase_id`       | INT          | -            | No (FK)     | References the phase to which the material is assigned.|
| `material_id`    | INT          | -            | No (FK)     | References the material used in this phase.            |
| `quantity_used`  | INT          | -            | No          | Quantity of the material required for this phase.      |

**Description**: Links specific materials to project phases, indicating the quantity of each material used in a particular phase.

---

### **Relationships**

- **Owners** to **Construction Projects**: One-to-Many (One owner may finance multiple projects, but each project has a single owner).
- **Construction Projects** to **Project Phases**: One-to-Many (Each project consists of multiple phases, but each phase belongs to one project).
- **Project Phases** to **Phase Materials**: One-to-Many (Each phase may require multiple types of materials, but each entry in Phase Materials is associated with a specific phase).
- **Resources and Materials** to **Phase Materials**: One-to-Many (Each material can be used in multiple phases, but each entry in Phase Materials references a single material).
