import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import pandas as pd
import requests

load_dotenv()

db_username=os.environ.get('db_username')
db_password=os.environ.get('db_password')
db_host=os.environ.get('db_host')
db_port=os.environ.get('db_port')
db_name=os.environ.get('db_name')

item = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
perk = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json"



def create_db_connection_string(db_username, db_password, db_host, db_port, db_name):
    connection_url = 'postgresql+psycopg2://'+ db_username + ':' + db_password + '@' + db_host + ':' + db_port +'/' + db_name
    print(connection_url)
    return connection_url

@st.cache_data
def load_data():
    conn_url = create_db_connection_string(db_username, db_password, db_host, db_port, db_name)
    db_engine = create_engine(conn_url, pool_recycle=3600)
    query="""
    SELECT *
    FROM student.lol_analytics
    """
    return pd.read_sql_query(query, con=db_engine)


def json_extract(obj, key):
    
    arr=[]
    
    def extract(obj, arr, key):
        if isinstance(obj,dict):
            for k, v in obj.items():
                if k == key:
                    arr.append(v)
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
                
        return arr
    values = extract(obj, arr, key)
    return values

@st.cache_data
def get_items():
    item_json = requests.get(item).json()
    item_ids = json_extract(item_json, 'id')
    item_names = json_extract(item_json, 'name')
    return dict(map(lambda i, j : (int(i),j),item_ids, item_names))

@st.cache_data
def get_perks():
    perk_json = requests.get(perk).json()
    perk_ids = json_extract(perk_json, 'id')
    perk_names = json_extract(perk_json, 'name')
    return dict(map(lambda i, j : (int(i),j),perk_ids, perk_names))


item_dict = get_items()
perk_dict = get_perks()


  
item_dict = {str(k): v for k, v in item_dict.items()}
perk_dict = {str(k): v for k, v in perk_dict.items()}
    
df = load_data()




columns_to_replace = ["item0", "item1", "item2", "item3", "item4", "item5", "item6"]


df[columns_to_replace] = df[columns_to_replace].replace(item_dict)



columns_to_replace = ['primary_keystone','primary_perk_1','primary_perk_2','primary_perk_3','secondary_perk_1','secondary_perk_2','offense','flex','defense']
df[columns_to_replace] = df[columns_to_replace].replace(perk_dict)



player_info = {
    'Faker':{
        'name': 'Lee Sang-hyeok (이상혁)',
        'age': 28,
        'team': 'T1',
        'country of birth': 'South'     
    },
    'Caps': {
        'name': 'Rasmus Borregaard Winther',
        'age': 25,
        'team': 'G2',
        'country of birth': 'Denmark'
    },
    'Palafox': {
        'name': 'Cristian Palafox',
        'age': 25,
        'team': 'Shopify Rebellion',
        'country of birth': 'United States'
    },
    'Chovy': {
        'name': 'Jeong Ji-hoon (정지훈)',
        'age': 23,
        'team': 'Gen.G',
        'country of birth': 'South Korea'
    },
    'Doinb': {
        'name': '	Kim Tae-sang (김태상)',
        'age': 28,
        'team': 'Ninjas in Pyjamas',
        'country of birth': 'South Korea'
    }
}


#change this later to work on puuid not riot id

df = df.replace({
    "riot_id": {
        "Hide on bush": "Faker",
        "G2 Caps": "Caps",
        "Palafoxy": "Palafox",
        "허거덩": "Chovy",
        "Heart": "Doinb"
    }
})


def render_table_without_index(df):
        return df.to_html(index=False, escape=False)
    


# df = df.replace("Hide on bush", "Faker")
# df = df.replace("G2 Caps", "Caps")
# df = df.replace("Palafoxy", "Palafox")
# df = df.replace("허거덩", "Chovy")
# df = df.replace("Heart", "Doinb")

stats = (
    df.groupby(['riot_id', 'champ_name'])
    .agg(
        pick_rate=('champ_name', 'count'), 
        wins=('win', lambda x: (x == True).sum()),  
        loses=('win', lambda x: (x == False).sum()),
        kills = ('kills', 'sum'),
        assists = ('assists', 'sum'),
        deaths = ('deaths', 'sum'),  
    )
    .reset_index()  # Reset index to convert groupby object back to DataFrame
)

stats['win_rate'] = (stats['wins'] / stats['pick_rate']) * 100
stats['KDA'] = (stats['kills'] + stats['assists']) / stats['deaths']


tab1, tab2 = st.tabs(['Player information', 'Champion information'])

with tab1:

    player = st.selectbox("Choose a player", ("Faker", "Chovy", "Doinb", "Caps", "Palafox"))
    
    filtered_stats = (stats[stats['riot_id'] == player].sort_values(by='pick_rate', ascending=False).drop(columns=['riot_id']).reset_index(drop=True))

    order = st.selectbox('Choose how to order the table', ('pick_rate', 'wins', 'loses', 'kills', 'assists', 'deaths', 'win_rate', 'KDA'))
    
    st.markdown(
        render_table_without_index(filtered_stats.sort_values(by=order, ascending=False)),
        unsafe_allow_html=True
    )

    st.write(f"Total games played: {filtered_stats['pick_rate'].sum()}")



    player_champion = st.selectbox("Choose a champion", tuple(df['champ_name'].drop_duplicates().tolist()))

    st.write(stats[stats['champ_name'] == player_champion])
    st.bar_chart(data=stats[stats['champ_name'] == player_champion], x='riot_id', y='win_rate')

    columns = ['champ_level','win','game_duration', 'kills', 'assists', 'deaths', 'cs', 'gold_earned', 'item0', 'item1', 'item2', 'item3', 'item4', 'item5', 'item6', 'primary_keystone', 'primary_perk_1', 'primary_perk_2', 'primary_perk_3', 'secondary_perk_1','secondary_perk_2', 'offense', 'flex', 'defense', 'total_damage_dealt']

    with st.expander("Caps"):
        filtered_champ_caps = df[(df['riot_id'] == 'Caps') & (df['champ_name'] == player_champion)]
        st.write(filtered_champ_caps[columns])
        
    with st.expander("Chovy"):
        filtered_champ_chovy = df[(df['riot_id'] == 'Chovy') & (df['champ_name'] == player_champion)]
        st.write(filtered_champ_chovy[columns])
        
    with st.expander("Faker"):
        filtered_champ_faker = df[(df['riot_id'] == 'Faker') & (df['champ_name'] == player_champion)]
        st.write(filtered_champ_faker[columns])
        
    with st.expander("Palafox"):
        filtered_champ_palafox = df[(df['riot_id'] == 'Palafox') & (df['champ_name'] == player_champion)]
        st.write(filtered_champ_palafox[columns])
        
    with st.expander("Doinb"):
        filtered_champ_doinb = df[(df['riot_id'] == 'Doinb') & (df['champ_name'] == player_champion)]
        st.write(filtered_champ_doinb[columns])
        
    


with tab2:
    champion = st.selectbox("Choose a champion", tuple(df[df['riot_id'] == player]['champ_name'].drop_duplicates().tolist()))
    st.write(df[df['champ_name'] == champion])
    st.write(f"Win rate: {df["win"].mean()*100}")
    item_columns = ["item0", "item1","item2","item3", "item4","item5"]
    all_items = df[df['champ_name'] == champion][item_columns].values.flatten()
    item_counts = pd.Series(all_items).value_counts()
    
    item_percentages = (item_counts/len(df[df['champ_name'] == champion])) * 100

    results = pd.DataFrame({
        "Amount purchased": item_counts,
        "Percentage of Games %": item_percentages
    })

    st.write("Common Items")
    st.write(results)

with st.sidebar:
    
    st.header(player)
    st.write(f"Player's name: {player_info[player]['name']}")
    st.write(f"Player's age: {player_info[player]['age']}")
    st.write(f"Player's team: {player_info[player]['team']}")
    st.write(f"Player's Country of Birth: {player_info[player]['country of birth']}")
    
    
    st.write("Most played champions")
    
    
    st.markdown(
        render_table_without_index(filtered_stats.drop(columns=['wins', 'loses', 'kills', 'assists', 'deaths']).head(5)),
        unsafe_allow_html=True
    )