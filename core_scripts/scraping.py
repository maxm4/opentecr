# -*- coding: utf-8 -*-
"""
Created on Mon May 16 09:24:58 2022

@author: Andrew Freiburger
"""
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pandas import DataFrame, read_csv, concat
from zipfile import ZipFile, ZIP_LZMA
from bs4 import BeautifulSoup
from warnings import warn
from datetime import date 
from glob import glob
from time import sleep
import requests
import numpy
import glob
import math, json, os, re

class TECR_scrape():
    def __init__(self, printing = True):
        # defining the website
        self.printing = printing
        root_url = "https://randr.nist.gov/enzyme/DataDetails.aspx?ID="
        end_url = "&finalterm=&data=enzyme"
        
        # identify the table and rows of pertinent data
        with open(os.path.join(os.path.dirname(__file__), 'Enzyme Thermodynamic Database.html'), 'r') as tecr_home_page:
            bs = BeautifulSoup(tecr_home_page, 'lxml')
        body = bs.find("table", attrs = {'id': 'MainBody_gvSearch'}).find_all("tr")
        total_entries = math.floor(1*len(body))

        # defining the boundaries of the dataframe section
        index_count = loop_count = name_iteration = 0
        output_loop = 1   
        
        # open the requests session
        session = requests.Session()
        adapter = HTTPAdapter(max_retries = Retry(connect=3, backoff_factor=0.5))
        session.mount('https://', adapter)

        # loop through the enzyme id values 
        if not os.path.exists('TECR_scraping'):
            os.mkdir('TECR_scraping')

        entry_dfs = []
        for id_row in range(1, total_entries):   
            id_value = body[id_row].find("a").text
            total_url = root_url + id_value + end_url
            bs = BeautifulSoup(session.get(total_url).text, 'lxml')
            
            # parsing the reaction names and strings   
            enzyme_name = body[id_row].find('span', attrs = {'id': 'MainBody_gvSearch_lblEnzyme_%s' %(name_iteration)}).text
            reaction = body[id_row].find('span', attrs = {'id': 'MainBody_gvSearch_lblReaction_%s' %(name_iteration)}).text
            name_iteration += 1
            
            ## first set of information 
            tables = bs.find_all("table", attrs={"id": "MainBody_DataList1"})
            if len(tables) == 0:
                warn(f'TECRError: The {id_value} reference {total_url} does not possess data.')
                continue
            body2 = tables[0].find_all("tr")
            body_rows2 = body2[1:]        
            information_entries_list, information_values_list, each_row2 = [], [], []
            for row in range(len(body_rows2)):
                for row_element in body_rows2[row].find_all("td"):
                    row_refined2 = re.sub("(\xa0)|(\n)|,","",row_element.text)
                    each_row2.append(row_refined2)

            column_count = 0
            for i, element in enumerate(each_row2):
                if i == 0 or i % 2 == 0:
                    information_entries_list.append(element)
                    column_count += 1
                else:
                    information_values_list.append(element)
                    column_count += 1
            column_count /= 2  #!!! why is the column count halved?
            
            table_df2 = DataFrame(
                data = [information_values_list], columns = information_entries_list, index = range(index_count, index_count+1)
                )
            table_df2.drop([table_df2.columns[-2], table_df2.columns[-1]], axis=1, inplace=True)
            
            ## second set of information 
            tables1 = bs.find_all("table", attrs = {"id": "MainBody_extraData"})
            if len(tables1) != 1:
                warn(f'The {id_value} reference {total_url} possesses an unexpected data structure.')
                continue
            if self.printing:
                print(id_value, f'\t\tloop: {loop_count}', f'\t\t{id_row}/{total_entries} enzymes', 
                      f'\t\t{index_count} datums', '\t\t\t\t', end = '\r')
            body1 = tables1[0].find_all("tr")
            heads, body_rows1 = body1[0], body1[1:]
            headings = ['Enzyme:', 'Reaction:']
            for head in heads.find_all("th"):
                head = (head.text).rstrip("\n")
                headings.append(head)
        
            total_rows = []
            for row_number in range(len(body_rows1)):
                each_row = [enzyme_name, reaction]
                for row_element in body_rows1[row_number].find_all("td"):
                    row_refined = re.sub("(\xa0)|(\n)|,","",row_element.text)
                    each_row.append(row_refined)
                total_rows.append(each_row)
            
            table_df1 = DataFrame(
                data = total_rows, columns = headings, index = range(index_count, len(body_rows1)+index_count)
                )
            table_df1.drop(table_df1.columns[len(table_df1.columns)-1], axis=1, inplace=True)
            
            # merge current and existing dataframes 
            this_dataframe = table_df1.join(table_df2)
            this_dataframe.index.name = 'index'
            if loop_count == 0:
                old_dataframe = this_dataframe
                old_dataframe.index.name = 'index'
            elif loop_count > 0:
                common_columns = list(set(this_dataframe.columns) & set(old_dataframe.columns))  # intersection operator
                current_dataframe = old_dataframe.merge(this_dataframe, on = common_columns, how = 'outer')
                old_dataframe = current_dataframe  
                
            # export the dataframe 
            index_count += len(body_rows1)
            time_delay = max_referenes_per_csv = 0
            sleep(time_delay)
            if loop_count == max_referenes_per_csv:
                # id_value = re.sub('(/)', '-', id_value)
                # while os.path.exists(os.path.join('TECR_scraping', f'{id_value}_{output_loop}.csv')):
                #     output_loop += 1
                entry_dfs.append(old_dataframe)
                loop_count = 0 
            else:        
                loop_count += 1 
                
        # combine all of the dataframes
        combined_df = concat(entry_dfs)
        if self.printing:
            display(combined_df)
        
        # refine the dataframe 
        combined_df = combined_df.fillna('')
        middle_dataframe_columns = ['T(K)', 'pH ', 'K<sub>c</sub>\' ', 'δ<sub>r</sub>H\'<sup>o</sup>(kJ.mol<sup>-1</sup>)', 'Km\'']
        left_dataframe_columns = ['index', 'Enzyme:', 'Reaction:', 'Reference:', 'Reference ID:'] 
        right_dataframe_columns = list(set(combined_df.columns) - set(left_dataframe_columns) - set(middle_dataframe_columns))
        self.scraped_df = combined_df.reindex(
            columns = left_dataframe_columns + middle_dataframe_columns + right_dataframe_columns
            )
        
        # export the dataframe
        self.scraped_df.to_csv('TECRDB_scrape.csv')
        with ZipFile('TECRDB.zip', 'w', compression = ZIP_LZMA) as zip:
            zip.write('TECRDB_scrape.csv')
            os.remove('TECRDB_scrape.csv')

    def amalgamate(self,):
        def merge_cells(re_search, row_name, row):
            if re.search(re_search, this_column):
                solute = re.search(re_search, this_column).group(1)
                if row[this_column] != '':
                    if row[row_name] == '':
                        row[row_name] = row[this_column] + ' ' + solute
                    if row[this_column] != '':
                        if row[row_name] != (row[this_column] or row[this_column] + ' ' + solute):
                            row[row_name] = row[row_name]+' & '+row[this_column]+' '+solute
                if this_column !=  row_name:
                    combined_columns.add(this_column)
        
        df = self.scraped_df.astype(str)
        combined_columns = set()
        re_searches = {
            '(?i)(?!Km\')(^K)': 'K<sub>c</sub>\' ', 
            '(?!Km\')(ë«|Î\´|δ)': 'δ<sub>r</sub>H(cal)/kJ mol<sup>-1</sup>)',
            '(?!Km\')(I<sub>c)':'I<sub>c</sub>(mol dm<sup>-3</sup>)'
            }
        print('\nColumns:\n', '='*len('Columns:'))
        for this_column in df:
            print(this_column)
            for index, row in df.iterrows():
                # combine similar columns
                merge_cells('(?<=c\()(\w+\d?\+?)(?<!,)', 'c(glycerol,mol dm<sup>-3</sup>)', row)
                merge_cells('(?<=m\()(\w+\d?\+?)(?<!,)', 'm(MgCl2,mol.kg<sup>-1</sup>)', row)
                for re_search, row_name in re_searches.items():
                    merge_cells(re_search, row_name, row)
        
                if this_column in ['buffer(mol dm<sup>-3</sup>)', 'buffer and/or salt ', 'media ', 'buffer ']:
                    if row[this_column] != '':
                        if row['Buffer:'] == '':
                            row['Buffer:'] = row[this_column]
                        if row['Buffer:'] != '':
                            if not re.search(row[this_column], row['Buffer:']):
                                row['Buffer:'] = row['Buffer:'] + ' + ' + row[this_column]
                    if this_column !=  'Buffer:':
                        combined_columns.add(this_column)
        
                if this_column in ['salt ', 'cosolvent ', 'added solute ', 'protein ', 'added solute ', 
                                   'percent(dimethyl sulfoxide) ', 'p(MPa)', 'pMg ']:
                    if row[this_column] != '':
                        if ['solvent '] == '':
                            row['solvent '] = row[this_column]
                            if this_column == 'p(MPa)':
                                row['solvent '] = row[this_column] + ' megapascals'  
                            elif this_column == 'pMg ':
                                row['solvent '] = row[this_column] + ' = -log[Mg+2]'   
                            elif this_column == 'percent(dimethyl sulfoxide) ':
                                row['solvent '] = row[this_column] + ' % DMSO'   
                        else:
                            if not re.search(row[this_column], row['solvent ']):
                                row['solvent '] = row['solvent '] + '  +  ' + row[this_column]
        
                    if this_column !=  'solvent ':
                        combined_columns.add(this_column)
                    
        # rename the base columns
        df.rename(columns = {'c(glycerol,mol dm<sup>-3</sup>)':'solutes [mol / dm^3]', 
                             'I<sub>c</sub>(mol dm<sup>-3</sup>)':'Ionic strength [mol / dm^3]', 
                             'T(K)':'T [K]', 
                             'I<sub>m</sub>(mol.kg<sup>-1</sup>)':'Ionic strength [mol / kg]', 
                             'm(MgCl2,mol.kg<sup>-1</sup>)':'solutes [mol / kg]', 
                             'solvent ':'Experimental conditions', 
                             'K<sub>c</sub>\' ':'Keq', 
                             'δ<sub>r</sub>H(cal)/kJ mol<sup>-1</sup>)':'Enthalpy [kJ / mol]'
                             },
                  inplace = True)
                  
        # delete the combined columns and export
        print('\nCombined columns:')
        for column in combined_columns:
            del df[column]
            print(column)
        for column in df.columns:
            if re.search('|index|Unnamed', column):
                print(column)
                del df[column]
        self.amalgamated_df = df
        self.amalgamated_df.to_csv("amalgamated_TECR_scrape.csv")
        
        # acquire a list of all enzymes
        enzyme_list, enzymes = [], []
        for index, row in df.iterrows():
            if row['Enzyme:'] not in enzyme_list and row['Enzyme:'] != '':
                enzyme_list.append(row['Enzyme:'])      
        for original_enzyme in enzyme_list:
            enzymes.append(re.search('(\w.*)',original_enzyme).group())
            
        # count down for processing and organizing the data
        data_per_enzyme = {}
        total_entries, count = 3979, 1
        for enzyme in enzymes:
            print('The data is being assembled and organized ... {}/425'.format(count), end = '\r')
            
            # lists of the database variables
            keq_values_per_enzyme = []
            km_values_per_enzyme = []
            enthalpy_values_per_enzyme = []
            temperatures_per_enzyme = []
            phs_per_enzyme = []
            
            # lists of identifying whether the reference contains the identified variable 
            references_of_an_enzyme = []
            reaction_of_an_enzyme = []
            km_in_the_reference = []
            enthalpy_in_the_reference = []
            keqs_in_a_reference = []
            for index, row in df.iterrows():
                iteration = 0
                if row['Enzyme:'] == ' '+enzyme:
                    reaction_of_an_enzyme.append(row['Reaction:'])
                    references_of_an_enzyme.append('Ibid')
                    if row['Reference:'] != '':
                        references_of_an_enzyme[-1] = row['Reference:']
                    
                    # clean keqs are added to a list
                    keqs_in_a_reference.append(False)   
                    if row['Keq'] != '':
                        cleaned_keq = re.search('(\-?\d+\.?\d*)', row['Keq'])
                        keq_values_per_enzyme.append(float(cleaned_keq.group())) 
                        keqs_in_a_reference[-1] = True
                        temperatures_per_enzyme.append(row['T [K]'])
                        phs_per_enzyme.append('nan')
                        if df.at[index, 'pH '] != '':
                            phs_per_enzyme[-1] = row['pH ']
                        
                    # clean kms are added to a list
                    km_in_the_reference.append(False)
                    if row['Km'] != '':
                        cleaned_km = re.search('(\-?\d+\.?\d*)', row['Km'])
                        km_values_per_enzyme.append(float(cleaned_km.group())) 
                        km_in_the_reference[-1] = True
                        if row['Keq'] == '':
                            temperatures_per_enzyme.append(row['T [K]'])
                            phs_per_enzyme.append('nan')
                            if df.at[index, 'pH '] != '':
                                phs_per_enzyme[-1] = row['pH ']
                        
                    # clean enthalpy values are added to a list
                    enthalpy_in_the_reference.append(False)
                    if row['Enthalpy [kJ / mol]'] != '':
                        cleaned_enthalpy = re.search('(\-?\d+\.?\d*)', '%s' %(row['Enthalpy [kJ / mol]']))
                        enthalpy_in_the_reference[-1] = True
                        enthalpy_values_per_enzyme.append(float(cleaned_enthalpy.group())) 
                        if row['Keq'] == '' and row['Km'] == '':
                            temperatures_per_enzyme.append(row['T [K]'])
                            phs_per_enzyme.append('nan')
                            if row['pH '] != '':
                                phs_per_enzyme[-1] = row['pH ']
                        
                    #loop through the unlabeled rows of each enzyme
                    while df.at[index + iteration, 'Enzyme:'] == '':
                        keqs_in_a_reference.append(False)
                        if row['Keq'] != '':
                            cleaned_keq = re.search('(\-?\d+\.?\d*)', row['Keq'])
                            keq_values_per_enzyme.append(float(cleaned_keq.group())) 
                            keqs_in_a_reference[-1] = True
                            temperatures_per_enzyme.append(df.at[index, 'T [K]'])
                            phs_per_enzyme.append('nan')
                            if row['pH '] != '':
                                phs_per_enzyme[-1] = row['pH ']
                            
                        #clean kms are added to a list
                        km_in_the_reference.append(False)
                        if df.at[index, 'Km'] not in empty_cell:
                            cleaned_km = re.search('(\-?\d+\.?\d*)', '%s' %(df.at[index, 'Km']))
                            km_in_a_reference[-1] = True
                            km_values_per_enzyme.append(float(cleaned_km.group())) 
                            if df.at[index, 'Keq'] == '':
                                phs_per_enzyme.append('nan')
                                temperatures_per_enzyme.append(df.at[index, 'T [K]'])
                                if df.at[index, 'pH '] not in empty_cell:
                                    phs_per_enzyme[-1] = row['pH ']
                            
                        # clean enthalpy values are added to a list
                        enthalpy_in_the_reference.append(False)
                        if df.at[index, 'Enthalpy [kJ / mol]'] != '':
                            cleaned_ethalpy = re.search('(\-?\d+\.?\d*)', row['Enthalpy [kJ / mol]'])
                            enthalpy_in_the_reference[-1] = True
                            enthalpy_values_per_enzyme.append(float(cleaned_enthalpy.group())) 
                            if row['Keq'] == '' and row['Km'] == '':
                                temperatures_per_enzyme.append(row['T [K]'])
                                phs_per_enzyme.append('nan')
                                if row['pH '] != '':
                                    phs_per_enzyme.append(row['pH '])
                            
                        #proceed to the next loop
                        if iteration + index < total_entries:
                            iteration += 1
        
            # statistical processing of scraped values
            average_keq_per_enzyme = standard_deviation_keq_per_enzyme = average_km_per_enzyme = standard_deviation_km_per_enzyme = average_enthalpy_per_enzyme = standard_deviation_enthalpy_per_enzyme = 'nan' 
            if len(keq_values_per_enzyme) != 0:
                average_keq_per_enzyme = numpy.mean(keq_values_per_enzyme)
                standard_deviation_keq_per_enzyme = numpy.std(keq_values_per_enzyme) 
            if len(km_values_per_enzyme) != 0:
                average_km_per_enzyme = numpy.mean(km_values_per_enzyme)
                standard_deviation_km_per_enzyme = numpy.std(km_values_per_enzyme)
            if len(enthalpy_values_per_enzyme) != 0:
                average_enthalpy_per_enzyme = numpy.mean(enthalpy_values_per_enzyme)
                standard_deviation_enthalpy_per_enzyme = numpy.std(enthalpy_values_per_enzyme)                 
                
            #store the information into a nested dictionary structure
            data_per_enzyme[enzyme] = {'reaction':reaction_of_an_enzyme,
                                       'experimental temperatures':temperatures_per_enzyme,
                                       'experimental phs':phs_per_enzyme,
                                       'keq reference':references_of_an_enzyme,
                                       'Keq':{'keq values in the reference':keqs_in_a_reference,
                                              'keqs':keq_values_per_enzyme, 
                                              'keq quantity':len(keq_values_per_enzyme), 
                                              'keq average':average_keq_per_enzyme, 
                                              'keq standard deviation':standard_deviation_keq_per_enzyme
                                              },
                                       'Km':{'km values in the reference':km_in_the_reference,
                                             'km values':km_values_per_enzyme,
                                             'km average':average_km_per_enzyme,
                                             'km standard deviation':standard_deviation_km_per_enzyme
                                             },
                                       'Enthalpy':{'enthalpy values in the reference':enthalpy_in_the_reference,
                                                   'enthalpy values':enthalpy_values_per_enzyme,
                                                   'enthalpy average':average_enthalpy_per_enzyme,
                                                   'enthalpy standard deviation':standard_deviation_enthalpy_per_enzyme
                                                   }
                                      }
            count += 1
        
        #export the database dictionary as a JSON file
        with open('TECR_consolidated.json', 'w') as output:
            json.dump('TECR_consolidated.json', output, indent = 4)
        with ZipFile('TECRDB.zip', 'a', compression = ZIP_LZMA) as zip:
            zip.write('TECR_consolidated.json')
            os.remove('TECR_consolidated.json')
