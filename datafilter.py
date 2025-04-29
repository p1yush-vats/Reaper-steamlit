import pandas as pd
import streamlit as st

# Read data
Superstore_df = pd.read_csv('Sample_Superstore.csv', encoding='latin1')
Customer_df = pd.read_csv('Customers.csv')

# Preview data
st.write("**Superstore Data (First 100 rows):**")
st.dataframe(Superstore_df.head(100))

st.write("**Customer Data (First 100 rows):**")
st.dataframe(Customer_df.head(100))

# Replace Ship Mode values
valmap = {
    'Standard Class': 0,
    'First Class': 1,
    'Second Class': 2,
}
Superstore_df['Ship Mode'] = Superstore_df['Ship Mode'].replace(valmap)

# Remove duplicates based on 'Customer Name' and assign unique IDs
unique_superstore_df = Superstore_df.drop_duplicates(subset='Customer Name', keep='first').copy()
unique_superstore_df['CustomerID'] = range(1, len(unique_superstore_df) + 1)

# Merge data
data_to_add = Customer_df[['CustomerID', 'Annual Income', 'Spending Score', 'Family Size', 'Age']]
merge_df = pd.merge(unique_superstore_df, data_to_add, on='CustomerID')

# Preview merged data
st.write("**Merged Data (Top 100 rows):**")
st.dataframe(merge_df.head(100))

# Save the merged dataframe to CSV
merge_df.to_csv('testfile.csv', index=False)

# Inform user that the file has been saved
st.success("Merged data saved to 'testfile.csv'")
