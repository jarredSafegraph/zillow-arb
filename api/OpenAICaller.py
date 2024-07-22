from openai import OpenAI
import streamlit as st

class OpenAICaller():
    api_key = st.secrets["openai_api_key"]
    client = OpenAI(api_key=api_key)

    def summarize_df(self, df):
        df_string = df.head(100).to_string()

        messages = [
            {
                "role": "system",
                "content": "Please provide a summary on the properties noting that a lower relative value is better. Things to note: how many have a negative relative value, how many have a positive relative value, and lowest 3 relative values."
            },
            {
                "role": "user",
                "content": df_string
            }
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        summary_text = response.choices[0].message.content.strip()

        return summary_text
