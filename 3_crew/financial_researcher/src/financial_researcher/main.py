#!/usr/bin/env python
# src/financial_researcher/main.py
import os
import time
from financial_researcher.crew import ResearchCrew

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the research crew.
    """
    inputs = {
        'company': 'Apple'
    }

    # crew = ResearchCrew()

    # # Run research task first
    # result_research = crew.research_task().execute(inputs)
    
    # # Wait to avoid rate limits
    # time.sleep(25)  

    # # Run analysis task next
    # result_analysis = crew.analysis_task().execute(inputs)

    # # Print final report
    # print("\n\n=== FINAL REPORT ===\n\n")
    # print(result_analysis.raw)

    # print("\n\nReport has been saved to output/report.md")

    # Create and run the crew
    result = ResearchCrew().crew().kickoff(inputs=inputs)

    # Print the result
    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

    print("\n\nReport has been saved to output/report.md")

if __name__ == "__main__":
    run()