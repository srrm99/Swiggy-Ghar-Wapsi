import csv
import json
import random

def generate_dummy_data(filename="delhi_insights.csv", num_records=30):
    """Generates a CSV file with simulated conversation summary JSONs."""
    
    fieldnames = ['json_summary']
    reasons = ['Low Earnings', 'Working on other platforms', 'Personal Break', 'App Issue', 'Not interested anymore', 'Health Issue']
    sentiments = ['Positive', 'Neutral', 'Negative']
    return_interest = ['Yes', 'No', 'Maybe']
    takeaways = [
        "DE is looking for higher payouts per order.",
        "The app was crashing frequently during peak hours.",
        "Competitor (Zomato/Dunzo) is offering better incentives.",
        "DE went to their hometown for a family function.",
        "Found a different full-time job.",
        "Was unhappy with the support team's response time.",
        "Wants more flexible working hours."
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(num_records):
            reason = random.choice(reasons)
            interest = random.choice(return_interest)
            
            # Create a more realistic mentioned_issues object
            issues = {}
            if "Earnings" in reason:
                issues['low_earnings'] = True
            if "platforms" in reason:
                issues['working_with_competitor'] = True
            if "App" in reason:
                issues['app_issue'] = True
            if random.random() > 0.8: # Add some randomness
                issues['support_delay'] = True

            summary_obj = {
                "conversation_summary": f"DE was inactive due to {reason.lower()} but showed '{interest}' interest in returning.",
                "reason_for_inactivity": reason,
                "is_interested_in_returning": interest,
                "mentioned_issues": issues,
                "de_sentiment": random.choice(sentiments),
                "key_takeaways": random.sample(takeaways, k=random.randint(1, 2)),
                "needs_manual_follow_up": random.choice([True, False])
            }

            # Write the JSON object as a string into the CSV row
            writer.writerow({'json_summary': json.dumps(summary_obj)})

    print(f"Successfully generated {num_records} records in {filename}")

if __name__ == '__main__':
    generate_dummy_data() 