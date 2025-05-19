import time
import requests
import random
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

input_csv = Path('input_profiles.csv')
output_csv = Path('scraped_data.csv')

# Load input URLs (optional, for now hardcoded)
# df_input = pd.read_csv(input_csv, encoding='utf-8')
# profile_urls = df_input['Profile_URL'].tolist()
profile_urls = ["https://www.g2.com/products/waalaxy/reviews?page=29"]

cookies = {
    'user_credentials': 'aef024d5e14c489bd8e333308f0faa7f8a76d8445d9b36871066123fdf8286a5123da5f3fba9a9a0cdcb77a75c7557cb7071767666f0d0d91ba07f0155a83d42%3A%3A6013024',
    'datadome': '~Njcu6rPnX0F_Dck4gW0iMSsVTNRfh7hy09tNwU0fIhn6_6wUFfU~4CNdLqdxe9uN2stxtDeuKp1iHvlwI5O7OqoQWbr1FQ_HRi2A_cYjbXIVhlLsP57SYa5vLHWa~dI'
}

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.g2.com',
}

data = []

for url in profile_urls:
    current_page = 1  # Start with the first page

    while True:  # Loop indefinitely until the "Next" page is not found
        print(f"Scraping page {current_page}: {url}")
        try:
            response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all review containers
            reviews = soup.find_all('div', class_='paper__bd')
            print(f"Found {len(reviews)} reviews on page {current_page}")

            # Find all header sections that contain the reviewer profile link
            headers_info = soup.find_all('div', class_='paper__hd paper__hd--bordered')
            print(f"Found {len(headers_info)} header sections on page {current_page}")

            # Remove the first two reviews and headers
            reviews = reviews[2:]

            # Check that both lists now have the same length
            min_len = min(len(reviews), len(headers_info))

            # Loop through each review and header, ensuring proper pairing
            for review, header in zip(reviews[:min_len], headers_info[:min_len]):
                # Extract review title (if available)
                title_tag = review.find('div', class_='m-0 l2')
                review_title = title_tag.get_text(strip=True) if title_tag else 'N/A'

                # Extract review date (if available)
                date_tag = review.find('time')
                review_date = date_tag.get_text(strip=True) if date_tag else 'N/A'

                # Extract review body text
                review_body = ''
                body_sections = review.select('div[itemprop="reviewBody"] p.formatted-text')
                for section in body_sections:
                    review_body += section.get_text(" ", strip=True) + "\n"

                review_body = review_body.strip()

                # Extract reviewer profile URL from the header
                name_tag = header.select_one('a.link--header-color')
                reviewer_url = name_tag['href'] if name_tag else 'N/A'

                # Now scrape the reviewer profile page
                name = ""
                member_since = ""
                title = ""
                linkedin_url = ""
                company = ""
                badges = ""
                questions = ""
                votes = ""
                try:
                    res = requests.get(reviewer_url, cookies=cookies, headers=headers, timeout=10)
                    s = BeautifulSoup(res.text, 'html.parser')

                    name_tag = s.find('div', class_='l3 mb-0')
                    name = name_tag.get_text(strip=True) if name_tag else 'N/A'

                    member_tag = s.find('div', class_='text-sm text-gray-500')
                    member_since = member_tag.find('span').get_text(strip=True) if member_tag and member_tag.find('span') else 'N/A'

                    title_tag = s.find('span', class_='x-title')
                    title = title_tag.get_text(strip=True) if title_tag else 'N/A'

                    company_tag = s.find('span', class_='x-company')
                    company = company_tag.get_text(strip=True) if company_tag else 'N/A'

                    linkedin_div = s.find('div', class_='js-action', attrs={'data-clipboard-text': True})
                    linkedin_url = linkedin_div['data-clipboard-text'] if linkedin_div else 'N/A'

                    stats = s.find_all('span', class_='font-semibold c-purple-100')
                    reviews = badges = questions = votes = 'N/A'

                    for stat in stats:
                        text = stat.get_text(strip=True).lower()
                        if 'review' in text:
                            reviews = text
                        elif 'badge' in text:
                            badges = text
                        elif 'question' in text:
                            questions = text
                        elif 'vote' in text:
                            votes = text

                except Exception as e:
                    print(f"Error scraping reviewer profile {reviewer_url}: {e}")

                # Append the data for this review
                data.append({
                    'Reviewer Profile URL': reviewer_url,
                    'Review Title': review_title,
                    'Review Date': review_date,
                    'Review Text': review_body,
                    'Name': name,
                    'Member Since': member_since,
                    'Title': title,
                    'Company': company,
                    'LinkedIn': linkedin_url,
                    'Reviews': reviews,
                    'Badges': badges,
                    'Questions': questions,
                    'Votes': votes
                })

            # Check if there is a "Next" page and extract its URL
            next_page_tag = soup.find('a', class_='pagination__named-link js-log-click pjax', text='Next ›')
            if next_page_tag and 'href' in next_page_tag.attrs:
                next_page_url = next_page_tag['href']
                url = next_page_url  # Update the URL to the next page
                current_page += 1  # Increment the page counter
                print(f"Moving to the next page: {next_page_url}")
            else:
                print("No more pages to scrape.")
                break

            # Sleep between requests to avoid overloading the server
            time.sleep(random.randint(3, 6))

        except Exception as e:
            print(f"Error scraping page {current_page}: {e}")
            time.sleep(random.randint(2, 5))

# Save the results to a CSV file
df_output = pd.DataFrame(data)
df_output.to_csv(output_csv, index=False, encoding='utf-8-sig')
print(f"Scraping complete. Data saved to: {output_csv.resolve()}")