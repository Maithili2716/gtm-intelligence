# GTM Intelligence

> An AI-powered intelligence layer for understanding accounts, extracting evidence from business documents, and turning fragmented GTM data into actionable account intelligence.

## Overview

GTM Intelligence is an AI-native system designed to help Go-To-Market teams understand accounts beyond static CRM fields.

Traditional CRM systems store facts such as:

- Account name
- Industry
- Revenue
- Contacts
- Opportunities
- Deal stage

But the information required to make good GTM decisions is usually distributed across documents, account history, conversations, and other business signals.

GTM Intelligence creates an intelligence layer over this fragmented information.

Instead of asking an LLM to directly answer questions from raw data, the system uses a structured pipeline:

```text
Business Data
     │
     ▼
Signal Extraction
     │
     ▼
Evidence Layer
     │
     ▼
Account Intelligence
     │
     ├── Similar Cases
     ├── Expertise
     ├── Historical Context
     ├── Change Detection
     └── Account Signals
             │
             ▼
        Agent / LLM
             │
             ▼
      Actionable Insight



Core Idea:

                         ┌───────────────┐
                         │    Account    │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
          Documents           Signals          History
              │                  │                  │
              ▼                  ▼                  ▼
          Evidence          Changes          Similar Cases
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ▼
                         Account Intelligence
                                 │
                                 ▼
                              Agent
                                 │
                                 ▼
                            GTM Action

Architecture:

                               ┌─────────────────────┐
                         │     GTM Sources     │
                         │                     │
                         │ CRM / Documents /   │
                         │ Account Data / etc. │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Ingestion Layer   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Signal Extraction  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
             ┌────────────┐  ┌────────────┐  ┌──────────────┐
             │  Evidence  │  │  Account   │  │   Change     │
             │   Layer    │  │  Signals   │  │  Detection   │
             └─────┬──────┘  └─────┬──────┘  └──────┬───────┘
                   │               │                │
                   └───────────────┼────────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │  Intelligence Graph │
                         │                     │
                         │ Similar Cases       │
                         │ Expertise Graph     │
                         │ Account Context     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Agent Harness     │
                         │                     │
                         │ Tools + Retrieval   │
                         │ Reasoning + Memory  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    GTM Insights     │
                         └─────────────────────┘


