import streamlit as st
import pandas as pd
import math
from openpyxl.utils.dataframe import dataframe_to_rows
'''
def __init__(self,length,breadth,height):
    self.length=length
    self.breadth=breadth
    self.height=height
    '''


def mu(item, vol):
    if item > 0:
        return item * vol
    elif item < 0:
        return item * vol * -1

def cost(merged_df, l, b, h):
    v = l * b * h
    merged_df[f'L{l}B{b}H{h}'] = merged_df.apply(lambda row: wasted(row['tot item volume'], v)*0.00239692312 + count_boxes(row['tot item volume'], v)*2.0834 , axis=1)

def wasted(so_quantity, size):
    if size == 0:
        return 100
    a = so_quantity % size
    if a == 0:
        return a
    else:
        return size - a

def count_boxes(item_volume, box_volume):
    boxes_needed = math.ceil(item_volume / box_volume)
    return boxes_needed

def crate_optimization(dry_file, box_file):
    # Read the input files
    dry = pd.read_excel(dry_file)
    box = pd.read_excel(box_file)
    box['box volume'] = box.apply(lambda row: (row['Box L'] * row['Box B'] * row['Box H'])/1000, axis=1)
    box['item volume'] = box.apply(lambda row: (row['Length'] * row['Breadth'] * row['Height'])/1000, axis=1)
    box = box.dropna(subset=["box volume"])
    box = box.assign(Box_L=lambda row: row['Box L'] / 10)
    box = box.assign(Box_B=lambda row: row['Box B'] / 10)
    box = box.assign(Box_H=lambda row: row['Box H'] / 10)

    #code for box l,b,h
    volume=[]
    length=[]
    breadth=[]
    height=[]
    v=0
    for row in box.iterrows():
        v=row[1]["Box_L"]*row[1]["Box_B"]*row[1]["Box_H"]
        if v not in volume:
            volume.append(v)
            length.append(row[1]["Box_L"])
            breadth.append(row[1]["Box_B"])
            height.append(row[1]["Box_H"])
    


    merged_df = pd.merge(dry, box, on="Material Number", how="inner")
    merged_df['tot item volume'] = merged_df.apply(lambda row: mu(row['Billing QTY'], row['item volume']), axis=1)
    return merged_df,length,breadth,height

def calculate_cost(merged_df,length,breadth,height):
    '''
    length = [61,36,38,54,48,42,31,61,52,48,37,40,31,38,36,33,32,28,49,34,30,52]
    breadth =[40,25,34,35,34,33,21,41,28,28,27,20,22,27,28,25,28,22,34,24,21,31]
    height = [15,36,38,50,25,31,31,50,24,26,26,29,31,31,30,38,26,33,23,30,31,22]
'''

    merged_dry_box = []
    waste = 0
    count = 0
    for i in range(len(length)):
        l = length[i]
        b = breadth[i]
        h = height[i]
        cost(merged_df, l, b, h)

    a = []
    for i in range(len(length)):
        l = length[i]
        b = breadth[i]
        h = height[i]
        a.append(f'L{l}B{b}H{h}')
    grouped_df = merged_df.groupby("Material Description_x").agg({**{'Material Description_x': 'first'}, **{col: 'sum' for col in a}})
    data = grouped_df

    columns = data.columns[1:]
    data['lowest_cost'] = data[columns].idxmin(axis=1)
    data['lowest_cost'] = data['lowest_cost'].str.split('_', expand=True)[0]
    title = merged_df["Material Description_x"]
    d = {}
    for i in title:
        d[i] = 1 + d.get(i, 0)

    for index, row in data.iterrows():
        material_description = row["Material Description_x"]
        if material_description in d:
            count_value = d[material_description]
            data.loc[index, "count"] = count_value

    count = data["count"].sum()
    total_count = data.groupby("lowest_cost")["count"].transform("sum")
    data["percentage"] = total_count / count * 100

    return data

def main():
    st.title("Crate Optimization and Cost Calculation")

    # Add file upload buttons for dry and box files
    dry_file = st.file_uploader("Upload Dry Order History File", type="xlsx")
    box_file = st.file_uploader("Upload Box Dimensions File", type="xlsx")

    if dry_file and box_file:
        # Run the crate optimization and cost calculation functions
        merged_df,length,breadth,height = crate_optimization(dry_file, box_file)
        data = calculate_cost(merged_df,length,breadth,height)

        # Display the result
        st.write("Optimized Crate Usage and Cost Calculation Result:")
        st.dataframe(data)

        # Create a download button for the final_cost.xlsx file
        df = pd.DataFrame(data)

        # Create an Excel writer object
        excel_writer = pd.ExcelWriter('final_cost.xlsx', engine='xlsxwriter')

        # Write the DataFrame to the Excel file
        df.to_excel(excel_writer, index=False)

        # Save the Excel writer object
        excel_writer.save()

        # Create a download button
        from streamlit import download_button

        download_button(
            label='Download Final Cost File',
            data=open('final_cost.xlsx', 'rb'),
            file_name='final_cost.xlsx',
        )


if __name__ == "__main__":
    main()
