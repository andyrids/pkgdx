---
context-hierarchy: Layer 3
---

# IEEE 830

Software Requirement Specification (SRS) reference document.

## Structure

### (1) Introduction

- (1.1) Purpose
  - Describe SRS purpose
  - Describe intended audience
- (1.2) Scope
  - Identify the software product
  - Enumerate what the system will & will not do
  - Describe user classes & benefits for each
- (1.3) Definitions. Acronyms & Abbreviations
  - Define SRS vocabulary
- (1.4) References
  - List all referenced documents including sources
- (1.5) Overview
  - Describe the content of the rest of the SRS
  - Describe how the SRS is organised
- (1.6) Risk Analysis
  - Describe the conclusions of risk analysis from using a risk template

### (2) Overall Description

- (2.1) Product Perspective
  - Present the business case and operational concept of the system
  - Describe how the proposed system fits into its context
  - Describe external interfaces; system, user, hardware, software, communication
  - Describe constraints; memory, operational
- (2.2) Product Functions
  - Summarise the major functional capabilities
  - Include Use Case Diagram and supporting narrative
  - Include Data Flow Diagram, if appropriate
- (2.3) User Characteristics
  - Describe and justify technical skills and capabilities of each user class
- (2.4) Constraints
  - Describe other constraints that will limit developer's options
- (2.5) Assumptions and Dependencies
  - List each of the factors that affect the requirements stated
- (2.6) Apportioning of Requirements
  - Identify requirements that may be delayed until future versions

### (3) Specific requirements

- Specify software requirements in sufficient detail to:
  - Enable a system design to satisfy them
  - Enable testing to verify them
- State requirements that are externally perceivable by users, operators, or externally connected systems
- Requirements should at a minimum, describe:
  - Every input (stimulus)
  - Every output (response)
  - Functions performed in response to input/output
- Requirements should:
  - Have characteristics of high quality requirements
  - Be cross-referenced to their source
  - Be uniquely identifiable
  - Be organised to maximize readability

- (3.1) External Interfaces
  - Detail inputs/outputs (complement, not duplicate, information presented in section 2)
- (3.2) Functions
  - Include detailed specifications of each use case, including collaboration and other diagrams
   useful for this purpose
- (3.3) Performance Requirements
  - Include the static and the dynamic numerical requirements placed on the software or on human
   interaction with the software as a whole
- (3.4) Logical Database Requirements
  - Include types of information used
  - Include data entities and their relationships
- (3.5) Design Constraints
  - Specify design constraints that can be imposed by other standards, hardware limitations, etc.
  - Report format
  - Data naming
- (3.6) Software System Attributes
  - Reliability, Availability, Security, Maintainability, Portability
- (3.7) Organising the specific requirements
  - The main body of requirements organised in a variety of possible ways:
    - Architecture Specification
    - Class Diagram
    - State and Collaboration Diagrams
    - Activity Diagram

## Quality

1. Correct: Requirement accurately reflects the user's needs
2. Unambiguous: Requirement have only one interpretation
3. Complete: Covers all valid/invalid inputs, conditions & responses
4. Consistent: Requirements do not conflict
5. Ranked for Importance & Stability: Requirements are classified by criticality (essential,
conditional, optional) and the likelihood of change
6. Verifiable: Requirement can be tested through inspection, analysis, demonstration or testing
7. Modifiable: Structured to facilitate changes
8. Traceable: Requirement have unique identifiers for tracking throughout the development
