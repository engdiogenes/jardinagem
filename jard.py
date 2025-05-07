import streamlit as st
import folium
from datetime import datetime
from branca.element import Template, MacroElement
import pandas as pd
import io
from streamlit_folium import folium_static
import json
import os
import matplotlib.pyplot as plt

def load_area_config():
    if os.path.exists("area_config.json"):
        with open("area_config.json", "r") as f:
            return json.load(f)
    return None

def save_area_config(config):
    with open("area_config.json", "w") as f:
        json.dump(config, f, indent=4)

# Função para converter mês em português para número
def mes_para_numero(mes):
    meses_pt = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    return meses_pt[mes]

# Configuração inicial do Streamlit
st.set_page_config(layout="wide")

# Inicialização segura do session_state
if "area_info" not in st.session_state:
    area_config = load_area_config()
    if area_config:
        st.session_state.area_info = area_config
    else:
        st.session_state.area_info = [
            {
                "nome": f"Área {i+1}",
                "maquina": "Trator",
                "periodo_chuvoso": 30,
                "periodo_seco": 60
            } for i in range(35)
        ]

if "meses_chuvosos" not in st.session_state:
    st.session_state.meses_chuvosos = ["Janeiro", "Fevereiro", "Março", "Dezembro"]

if "default_color" not in st.session_state:
    st.session_state.default_color = "#90EE90"

if "max_days" not in st.session_state:
    st.session_state.max_days = 90

# Escala de cores padrão
default_colors = {
    0: '#90EE90', 5: '#A8E05F', 10: '#C0D94B', 15: '#D8C93A', 20: '#E8B930',
    25: '#F0A830', 30: '#F7982F', 35: '#F87C2C', 40: '#F95F2A', 45: '#FA4327',
    50: '#FB2A26', 55: '#FC1A24', 60: '#FD0F23', 65: '#E00D20', 70: '#C10B1D',
    75: '#A3091A', 80: '#850717', 85: '#670514', 90: '#490311'
}

def get_color(cut_date, colors):
    cut_date = datetime.combine(cut_date, datetime.min.time())
    days_since_cut = (datetime.now() - cut_date).days
    for days in range(0, st.session_state.get("max_days", 90) + 1, 5):
        if days_since_cut <= days:
            return colors.get(days, st.session_state.get("default_color", "#90EE90"))
    return colors.get(90, st.session_state.get("default_color", "#90EE90"))

def get_status(days_since_cut, chuvoso, seco):
    current_month = datetime.now().month
    meses_chuvosos = [mes_para_numero(month) for month in st.session_state.meses_chuvosos]
    periodicidade = chuvoso if current_month in meses_chuvosos else seco
    return "Vencido" if days_since_cut > periodicidade else "Em dia"

# Sidebar
page = st.sidebar.radio("Navegar para:", ["Mapa", "Configuração", "Histórico de Cortes"])

# Página de configuração
if page == "Configuração":
    st.title("Configuração das Áreas")

    st.session_state["default_color"] = st.color_picker(
        "Cor padrão para áreas sem corte",
        st.session_state.get("default_color", "#90EE90")
    )

    st.session_state["max_days"] = st.slider(
        "Número máximo de dias para escala de cores",
        30, 120, st.session_state.get("max_days", 90)
    )

    st.session_state.meses_chuvosos = st.multiselect(
        "Meses considerados chuvosos",
        options=[
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ],
        default=st.session_state.meses_chuvosos
    )

    for i in range(35):
        with st.expander(f"Configuração da Área {i+1}", expanded=False):
            st.session_state.area_info[i]["nome"] = st.text_input(
                f"Nome da Área {i+1}",
                value=st.session_state.area_info[i]["nome"],
                key=f"nome_{i}"
            )

            st.session_state.area_info[i]["maquina"] = st.selectbox(
                f"Máquina utilizada na Área {i+1}",
                ["Trator", "Girozero", "Roçadeira"],
                index=["Trator", "Girozero", "Roçadeira"].index(
                    st.session_state.area_info[i]["maquina"]
                ),
                key=f"maquina_{i}"
            )

            st.session_state.area_info[i]["periodo_chuvoso"] = st.number_input(
                f"Periodicidade de corte no período chuvoso (dias) - Área {i+1}",
                min_value=1, max_value=180,
                value=st.session_state.area_info[i]["periodo_chuvoso"],
                key=f"chuvoso_{i}"
            )

            st.session_state.area_info[i]["periodo_seco"] = st.number_input(
                f"Periodicidade de corte no período seco (dias) - Área {i+1}",
                min_value=1, max_value=180,
                value=st.session_state.area_info[i]["periodo_seco"],
                key=f"seco_{i}"
            )

    st.success("Configurações atualizadas com sucesso!")
    # Salvar configurações ao final da aba de configuração
    save_area_config(st.session_state.area_info)

# Página do mapa
elif page == "Mapa":
    st.title("Mapa de gestão de corte de vegetação")

    # Baixar modelo de CSV
    st.markdown("### 📄 Baixe o modelo de preenchimento:")
    modelo_df = pd.DataFrame({
        "area": list(range(1, 36)),
        "data_corte": ["2025-03-01"] * 35
    })
    csv_modelo = io.StringIO()
    modelo_df.to_csv(csv_modelo, index=False)
    st.download_button(
        label="📥 Baixar modelo de CSV",
        data=csv_modelo.getvalue(),
        file_name="modelo_corte_vegetacao.csv",
        mime="text/csv"
    )

    # Upload do CSV
    uploaded_file = st.file_uploader("📤 Envie o arquivo CSV com as datas de corte", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "area" not in df.columns or "data_corte" not in df.columns:
            st.error("CSV inválido. As colunas devem ser: 'area' e 'data_corte'")
        else:
            df["data_corte"] = pd.to_datetime(df["data_corte"],errors='coerce')
            if df["data_corte"].isnull().any():
                st.warning("Algumas datas estão inválidas no CSV.")
            else:
                min_days = st.slider("Mostrar áreas com no mínimo X dias desde o corte", 0, st.session_state.get("max_days", 90), 0)

                # Coordenadas das áreas (exemplo fictício)
                area_coords = [
# P1E-A
[[-22.4892150101985, -44.53628944378521],
[-22.488604361891028, -44.53657005393111],
[-22.48814149209604, -44.53662076205793],
[-22.488015963496707, -44.536512676664415],
[-22.487838801754915, -44.53653821388996],
[-22.487717535889715, -44.53672257511488],
[-22.487176722014723, -44.53693299825759],
[-22.486776264458264, -44.53721849833907],
[-22.486676454201298, -44.53706943988472],
[-22.487114212624817, -44.53674970934726],
[-22.487645450985507, -44.53657030709373],
[-22.487770497958074, -44.5364104003999],
[-22.488006926312046, -44.536365605212985],
[-22.48821775541626, -44.53645519867187],
[-22.488241286909652, -44.53645519849039],
[-22.488476601062555, -44.53641686907708],
[-22.48857304959472, -44.53600757079865],
[-22.488597325337707, -44.53599462982132],
[-22.488597126599295, -44.535572528627426],
[-22.48862632083402, -44.53556629190863],
[-22.488626321101282, -44.53534246508779],
[-22.48881395971028, -44.535304859951296],
[-22.48915139557624, -44.535944961705205],
[-22.48921501020765, -44.53629581865389]],
#P1E-B
[[-22.486778520115617, -44.537278476245895],
[-22.48559616597879, -44.538019642740565],
[-22.484499657607106, -44.538795533316026],
[-22.483965503003756, -44.53931204893238],
[-22.48375702841266, -44.53962088851651],
[-22.483608567708938, -44.53986039733368],
[-22.483484248982972, -44.5395678148144],
[-22.48372288851175, -44.53900692188699],
[-22.484126054394405, -44.53854457279756],
[-22.48488933951751, -44.53812494767339],
[-22.485402396503503, -44.53774687826876],
[-22.486025436065763, -44.53727818444819],
[-22.486521678238965, -44.5371897784923],
[-22.48670248404335, -44.53706256905197]],
# P1E-C
[[-22.48688243657907, -44.53818451182176],
[-22.48681126576883, -44.537528960222275],
[-22.486899266919817, -44.5373808462416],
[-22.486838257269778, -44.53727469711381],
[-22.484536402494797, -44.53886914384722],
[-22.48610978450587, -44.53856900543562],
[-22.486197957702615, -44.538888518656044],
[-22.486316890203167, -44.53917131319824],
[-22.486552961923554, -44.53916806967983],
[-22.486708920906374, -44.53909340920772],
[-22.486669437714838, -44.538875726014794],
[-22.486500957480317, -44.53894576916969],
[-22.486500157095893, -44.53893949492973],
[-22.486440750581576, -44.53828906734141],
[-22.48691227076902, -44.53818644472393],
[-22.486894045943245, -44.53818277411627]],
# P1E-D
[[-22.48697601918495, -44.541637032359176],
[-22.486704085037264, -44.53912328668172],
[-22.48632473613282, -44.5391901862012],
[-22.486258964818095, -44.53890865083509],
[-22.485951379022218, -44.5386850819178],
[-22.484966541840002, -44.53885408562257],
[-22.484955411667798, -44.53884496726523],
[-22.484714717223433, -44.5389888456226],
[-22.48475779712686, -44.53971574662274],
[-22.4854701366647, -44.541313073641376],
[-22.485752372877478, -44.54195988661638],
[-22.487006639604125, -44.54164314642328]],
# P1E-E
[[-22.484602823136807, -44.53890159974378],
[-22.484698153577888, -44.53975054978894],
[-22.484693952822806, -44.53995487877751],
[-22.48395847243147, -44.54005307942218],
[-22.483813795783753, -44.53972266827471],
[-22.484235425950335, -44.5391480040603],
[-22.484614304782628, -44.538921999765925]],
# P1E-F
[[-22.484661161978778, -44.5399082503027],
[-22.486055958591997, -44.543122965723605],
[-22.485886503968832, -44.54333021586312],
[-22.48457797670264, -44.54027552891268],
[-22.48401397936359, -44.5402501068354],
[-22.483942041673636, -44.54002282246162],
[-22.484650212099073, -44.539940108608384]],
# P1E-G
[[-22.48609986921309, -44.543104468700406],
[-22.489512283685496, -44.542623477875345],
[-22.489802554814727, -44.54294138583691],
[-22.485932030793357, -44.54341178113289]],

#P1E-H
[[-22.489506776184875, -44.542570101790176],
[-22.489482166345464, -44.54140843410614],
[-22.48567259641259, -44.5419183654847],
[-22.48618151138955, -44.54301440264202],
[-22.48951059429305, -44.542524561141]],

#P2E-A
[[-22.489739199858068, -44.54264213712882],
[-22.49213426843662, -44.5423628988837],
[-22.492195139413383, -44.54264457904935],
[-22.48976942685133, -44.542863879012174]],

#P2E-B
[[-22.48974832282247, -44.54265010255431],
[-22.49213467465016, -44.542381315777014],
[-22.491937362175246, -44.54104976255741],
[-22.49153823806687, -44.54101433336423],
[-22.491271044558292, -44.54118985692881],
[-22.48958088902175, -44.54147810558138],
[-22.489715346303935, -44.54265397134658]],

#P2E-C
[[-22.49260490804964, -44.542706295356034],
[-22.492423477925776, -44.54104602256193],
[-22.49212250370988, -44.54049357547612],
[-22.491720423807692, -44.54064920980403],
[-22.48946078111849, -44.54078817237485],
[-22.489562820101526, -44.541380915573],
[-22.491326964221045, -44.5411560635184],
[-22.49148789448892, -44.541001779496845],
[-22.49184311157794, -44.540915195782496],
[-22.49200003594716, -44.54098719515164],
[-22.49211525277076, -44.542428165484786],
[-22.492141287578924, -44.54269579456053],
[-22.49260395391111, -44.54267142849747]],

#P2E-D
[[-22.49225291087156, -44.54039883962764],
[-22.49085172024787, -44.538006282285565],
[-22.490447955070753, -44.538225536506296],
[-22.49076036650574, -44.540762078520636],
[-22.491659425691658, -44.54073022173363],
[-22.492210471461373, -44.540394616973366]],

#P2E-E
[[-22.49063652198091, -44.540771984430904],
[-22.490465906187268, -44.538210955013284],
[-22.490808050705013, -44.53798899956388],
[-22.490579220894613, -44.5374255588925],
[-22.489238394653693, -44.538339437102586],
[-22.489483388818858, -44.54102416842607],
[-22.490695816127033, -44.540816803893094]],

# P2E-F
[[-22.490582199815204, -44.537515988606955],
[-22.490510053950015, -44.53735543645934],
[-22.489244277805007, -44.53808646404648],
[-22.489286688220872, -44.53834793186706]],

#P2E-G
[[-22.489231995840925, -44.53849576033275],
[-22.489431929274385, -44.541407323503535],
[-22.486984593188556, -44.54171635387721],
[-22.486818984791054, -44.54057236945579],
[-22.488980427932432, -44.540375866873546],
[-22.48894244349655, -44.538558623451614],
[-22.48928953670181, -44.53847812603966]],

#P2E-H

[[-22.48830975972828, -44.538268895916225],
[-22.48818731780736, -44.53691499718957],
[-22.487529357980435, -44.5369444540363],
[-22.486849196606503, -44.53742611971208],
[-22.48690838569744, -44.53841356194507],
[-22.48831961907706, -44.53824261787658]],

#P2E-I

[[-22.489162682536538, -44.5373812185006],
[-22.489263391704803, -44.538442154278336],
[-22.486982532724888, -44.5387764800269],
[-22.48693361070899, -44.53843687883168],
[-22.48833313396873, -44.53826690597478],
[-22.48824093109627, -44.537485354095296],
[-22.48920596535845, -44.53732618908306]],

#P1W-A

[[-22.49188481164542, -44.54492881597283],
[-22.49168978314756, -44.54327021295797],
[-22.490050578650262, -44.54346665718088],
[-22.490047279634965, -44.543729084359676],
[-22.48942328165687, -44.543817377936556],
[-22.48950198061829, -44.54469806287458],
[-22.489543394029276, -44.54512739614259],
[-22.490298084836127, -44.54497637202184],
[-22.4903827277616, -44.545411115500535],
[-22.491938133673088, -44.544981009025584]],

# P1W-B

[[-22.491793494179742, -44.54333006639081],
[-22.49175896478048, -44.543137023535714],
[-22.491691913386347, -44.54246142647005],
[-22.49011071388118, -44.5426402990202],
[-22.49019239204128, -44.542888638218166],
[-22.48924950293641, -44.54300477552774],
[-22.489386194969867, -44.543777253993106],
[-22.49002882637237, -44.543759074017565],
[-22.490016904203472, -44.543487244461105],
[-22.491787454824372, -44.543406693312996],
[-22.491714977192114, -44.54312731877908]],

# P2W-A

[[-22.48927971330925, -44.54383582190185],
[-22.48925410370876, -44.54277624102222],
[-22.487316589210177, -44.543029016245534],
[-22.487476184361046, -44.54414818554068],
[-22.48931513883151, -44.54390731779081]],

# P2W-B

[[-22.48951537932026, -44.54581046160085],
[-22.48923186458569, -44.54391751049694],
[-22.487580939290858, -44.54421115738727],
[-22.487608020206522, -44.5454062679654],
[-22.48811531651974, -44.54596674558749],
[-22.48957568780795, -44.545848848019595]],

#P3W-A

[[-22.487334004677034, -44.543194182325614],
[-22.487325678353614, -44.54298222223566],
[-22.486029730409598, -44.543187744798864],
[-22.485113340818575, -44.54366456323263],
[-22.48543566673846, -44.54409501276961],
[-22.48689243281423, -44.543263548422445],
[-22.4872723008852, -44.54314097792242]],

# P3W-B

[[-22.48538385902925, -44.54413176302442],
[-22.485258060911292, -44.54370748986745],
[-22.48422384283112, -44.544289337335556],
[-22.484406551260154, -44.54464585525061]],

# P3W-C

[[-22.487360445138908, -44.54387293629455],
[-22.487301312122522, -44.54341433051533],
[-22.48719150355547, -44.54331911705672],
[-22.48699566381282, -44.543311570350575],
[-22.48579857278907, -44.543981595931164],
[-22.486087492735184, -44.544545678058554],
[-22.486300346721176, -44.544442876988434],
[-22.48619402715585, -44.54421377753698],
[-22.48683574429521, -44.54387367049419],
[-22.486953277176976, -44.54392941393477],
[-22.4873631778269, -44.54384067598701]],

# P3W-D
[[-22.487457931582497, -44.54448540233586],
[-22.487385163105113, -44.543882637697514],
[-22.48697269386013, -44.54394615170048],
[-22.48686966167768, -44.54380583706863],
[-22.486174497025246, -44.54413967598955],
[-22.48630166179837, -44.54445545763214],
[-22.486093966208628, -44.544551254648496],
[-22.486314676741017, -44.5450848602224],
[-22.48744371280331, -44.54445546956461],
[-22.487377417412542, -44.54386444671886]],

# P3W-E
[[-22.4876033703913, -44.54558023864001],
[-22.487468421897407, -44.54445839208224],
[-22.48624757432335, -44.545122841836005],
[-22.486441257463692, -44.54544467738457],
[-22.48654340352991, -44.54536986351283],
[-22.486391211041614, -44.54512232450107],
[-22.48695416042601, -44.544818283625744],
[-22.48705856847858, -44.54498741520898],
[-22.48683010186261, -44.5451300727875],
[-22.48716142401928, -44.5457795760574],
[-22.4875971442698, -44.54558784696875],
[-22.487479667426513, -44.54447461871776]],

# P3W-F
[[-22.48632809326321, -44.54532537724833],
[-22.485989034063785, -44.544449382373585],
[-22.485693286400835, -44.5446067225644],
[-22.486118346450265, -44.545459319093055]],

# P3W-G
[[-22.485687356083183, -44.54455006665535],
[-22.485472949622284, -44.544142468013135],
[-22.48465956338426, -44.54463149506414],
[-22.484840030785257, -44.54506188013824]],

# P3W-H
[[-22.486509688915916, -44.54537283397347],
[-22.48637099684035, -44.54517316287623],
[-22.48628696468042, -44.54515798189869],
[-22.485986195625326, -44.54532235511452],
[-22.485593839919645, -44.545568071788324],
[-22.485278879855798, -44.54570214829912],
[-22.484962158125267, -44.54498922415829],
[-22.484849002031723, -44.54503489802833],
[-22.4852693657338, -44.546002500666965],
[-22.485711426092024, -44.545846763127685],
[-22.486314859912422, -44.54553691945306],
[-22.486498720206026, -44.545380553230125]],

# P4W-A

[[-22.486345452457172, -44.54583052230568],
[-22.486039325645688, -44.54598858907717],
[-22.485889604891433, -44.545742839256356],
[-22.48566227346259, -44.54589591071292],
[-22.485725776008508, -44.54608482857579],
[-22.485546710326897, -44.54615034324484],
[-22.485433315025823, -44.54601290594824],
[-22.48521072927347, -44.54614386241613],
[-22.484661486070237, -44.544830250057736],
[-22.484375203965676, -44.54498552181381],
[-22.48478770408721, -44.545811776735675],
[-22.48558823309536, -44.54698209864419],
[-22.486437931128986, -44.54655328217612],
[-22.486378704973866, -44.546417902194456],
[-22.486566401863683, -44.54625970949479],
[-22.486339850926463, -44.545803481438625]],

# P4W-B

[[-22.48774500733739, -44.54795344380928],
[-22.487632366654854, -44.547340046313685],
[-22.487469380341288, -44.54706443718995],
[-22.487035797616983, -44.547275933019534],
[-22.486731186769415, -44.54659468649175],
[-22.48704684160353, -44.54639112676571],
[-22.48693453867775, -44.54625933411809],
[-22.485658737788103, -44.54700117450361],
[-22.48627493938175, -44.547939500065446]],

# P4W-C
[[-22.48774741516519, -44.54796356522182],
[-22.487686865772517, -44.547297850424414],
[-22.487620469613788, -44.5470376484388],
[-22.487922269036208, -44.54683764377414],
[-22.487725470748245, -44.54647041972388],
[-22.48778262807537, -44.54627832627356],
[-22.48874993933501, -44.546049695241],
[-22.48885765434089, -44.54693629019929],
[-22.488567818816094, -44.546961305928775],
[-22.488731255392143, -44.547903878599364],
[-22.487774283450026, -44.54796424556957]],

# P4W-D

[[-22.489523944563167, -44.54598697464894],
[-22.48966518204239, -44.54650139105032],
[-22.48989556813947, -44.546907548930555],
[-22.490384870749192, -44.54766326348205],
[-22.490407110657074, -44.5477730519351],
[-22.489533274882476, -44.547790630822064],
[-22.48952482173048, -44.54718272713198],
[-22.489533470151702, -44.54597235843246]],

# P5W-A

[[-22.48969709096307, -44.54596761231146],
[-22.4897393408423, -44.54623005207035],
[-22.489947210109623, -44.54653318258873],
[-22.490062895913315, -44.546954143602576],
[-22.49047888474815, -44.54759476494059],
[-22.490620464363992, -44.5476957900116],
[-22.491464821293977, -44.547384304387364],
[-22.4925751897925, -44.547163670098705],
[-22.49385930076751, -44.5471287056881],
[-22.49356413354255, -44.5469973405924],
[-22.491662234232784, -44.546506147681036],
[-22.489676826180975, -44.54599063243632]],

# P5W-B

[[-22.490524384040537, -44.54606256141668],
[-22.493988182137866, -44.54709838222009],
[-22.494202183951206, -44.54694907282749],
[-22.494678588809432, -44.54657710798844],
[-22.494819938209805, -44.54578423967169],
[-22.494575310438297, -44.545023680472056],
[-22.493889050013784, -44.54490691918464],
[-22.49348979298541, -44.54516845097942],
[-22.49309959896442, -44.54597203777485],
[-22.492727515074066, -44.54622284619936],
[-22.492276047064742, -44.54606203759653],
[-22.491134478157377, -44.54583651744892],
[-22.490955854230524, -44.54601987414672],
[-22.490493142901922, -44.546087814604725]]]
                # Substitua com coordenadas reais

                m = folium.Map(location=[-22.4882, -44.5424], zoom_start=16.45)

                data = []
                for i in range(35):
                    row = df[df["area"] == i + 1]
                    if not row.empty and area_coords[i]:
                        data_corte = row.iloc[0]["data_corte"].date()
                        days_since_cut = (datetime.now().date() - data_corte).days
                        if days_since_cut >= min_days:
                            nome_area = st.session_state.area_info[i]["nome"]
                            maquina = st.session_state.area_info[i]["maquina"]
                            chuvoso = st.session_state.area_info[i]["periodo_chuvoso"]
                            seco = st.session_state.area_info[i]["periodo_seco"]
                            status = get_status(days_since_cut, chuvoso, seco)
                            folium.Polygon(
                                area_coords[i],
                                color=get_color(data_corte, default_colors),
                                fill=True,
                                fill_opacity=0.7,
                                popup=f"{nome_area}<br>{days_since_cut} dias desde o corte<br>Máquina: {maquina}<br>Status: {status}"
                            ).add_to(m)
                            data.append([nome_area, maquina, days_since_cut, chuvoso, seco, status, data_corte.strftime('%B')])

                # Legenda
                legend_html = '''
                <div style='position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius:5px; padding: 10px;'>
                <b>Legenda - Dias desde o corte</b><br>
                '''
                for days in range(0, st.session_state.get("max_days", 90) + 1, 15):
                    color = default_colors.get(days, st.session_state.get("default_color", "#C5F5C5"))
                    legend_html += f"<i style='background:{color};width:18px;height:18px;float:left;margin-right:8px;opacity:0.7;'></i>{days} dias<br>"
                legend_html += "</div>"

                legend = MacroElement()
                legend._template = Template(legend_html)
                m.get_root().add_child(legend)

                if data:
                    df_prioridade = pd.DataFrame(data, columns=[
                        "Nome da Área", "Máquina", "Dias desde o corte",
                        "Periodicidade Chuvoso", "Periodicidade Seco", "Status", "Mês do Último Corte"
                    ])
                    df_prioridade = df_prioridade.sort_values(by="Dias desde o corte", ascending=False)

                    st.markdown("### 📋 Ordem de Prioridade de Corte")
                    mes_atual = datetime.now().strftime('%B')
                    periodo_atual = "Chuvoso" if mes_atual in st.session_state.meses_chuvosos else "Seco"
                    st.markdown(f"Atualmente, estamos em período: **{periodo_atual}**")

                    def highlight_status(val):
                        if val == "Vencido":
                            return "background-color: red; color: black"
                        return ""

                    styled_df = df_prioridade.style.applymap(highlight_status, subset=["Status"])
                    st.dataframe(styled_df, use_container_width=True)

                    folium_static(m, width=1400, height=800)

                    if data and st.button("Exportar Relatório"):
                        df_export = pd.DataFrame(data, columns=[
                            "Nome da Área", "Máquina", "Dias desde o corte",
                            "Periodicidade Chuvoso", "Periodicidade Seco", "Status", "Mês do Último Corte"
                        ])
                        df_export.to_csv("relatorio_corte_vegetacao.csv", index=False)
                        st.success("Relatório exportado com sucesso!")

# Página do histórico de cortes
elif page == "Histórico de Cortes":
    st.title("📄 Histórico de Cortes Realizados")

    uploaded_file = st.file_uploader("📤 Envie o arquivo CSV com as datas de corte", type="csv", key="historico")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "area" not in df.columns or "data_corte" not in df.columns:
            st.error("CSV inválido. As colunas devem ser: 'area' e 'data_corte'")
        else:
            df['data_corte'] = pd.to_datetime(df['data_corte'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=["data_corte"])
            # Expandir todos os registros do CSV em vez de apenas o primeiro por área
            df["Data do Corte"] = pd.to_datetime(df["data_corte"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["Data do Corte"])

            # Mapear nomes e máquinas das áreas
            area_info = {i + 1: st.session_state.area_info[i] for i in range(35)}
            df["Área"] = df["area"].map(lambda x: area_info.get(x, {}).get("nome", f"Área {x}"))
            df["Máquina"] = df["area"].map(lambda x: area_info.get(x, {}).get("maquina", "Desconhecida"))
            df["Dias desde o Corte"] = (datetime.now().date() - df["Data do Corte"].dt.date).dt.days
            df["Status"] = df.apply(lambda row: get_status(
                row["Dias desde o Corte"],
                area_info.get(row["area"], {}).get("periodo_chuvoso", 30),
                area_info.get(row["area"], {}).get("periodo_seco", 60)
            ), axis=1)
            df["Período"] = "Chuvoso" if datetime.now().month in [mes_para_numero(m) for m in
                                                                  st.session_state.meses_chuvosos] else "Seco"

            df_hist = df[["Área", "Data do Corte", "Máquina", "Dias desde o Corte", "Status", "Período"]]

            styled_hist = df_hist.style.set_properties(**{'text-align': 'center'})
            st.dataframe(styled_hist, use_container_width=True)

            df_hist["Data do Corte"] = pd.to_datetime(df_hist["Data do Corte"], dayfirst=True, errors="coerce")

            # Adicionar filtros
            st.markdown("### Filtros")
            areas_selecionadas = st.multiselect(
                "Selecione as Áreas",
                options=df_hist["Área"].unique(),
                default=df_hist["Área"].unique()
            )

            data_inicio, data_fim = st.date_input(
                "Selecione o intervalo de datas",
                [df_hist["Data do Corte"].min(), df_hist["Data do Corte"].max()]
            )

            # Filtrar dados
            df_hist_filtrado = df_hist[
                (df_hist["Área"].isin(areas_selecionadas)) &
                (pd.to_datetime(df_hist["Data do Corte"], format="%d/%m/%Y") >= pd.to_datetime(data_inicio)) &
                (pd.to_datetime(df_hist["Data do Corte"], format="%d/%m/%Y") <= pd.to_datetime(data_fim))
                ]

            # Converter coluna de data para datetime
            df_hist["Data do Corte"] = pd.to_datetime(df_hist["Data do Corte"], format="%d/%m/%Y")


# Adicionar gráfico de linha do tempo abaixo da tabela
            if not df_hist_filtrado.empty:
                st.markdown("### 📈 Histórico de Cortes por Área (Dispersão)")
                fig, ax = plt.subplots(figsize=(12, 8))
                for area in df_hist_filtrado["Área"].unique():
                    area_data = df_hist_filtrado[df_hist_filtrado["Área"] == area]
                    ax.scatter(area_data["Data do Corte"], [area] * len(area_data), label=f'Área {area}')

                ax.set_xlabel("Data de Corte")
                ax.set_ylabel("Área")
                ax.set_title("Quantidade de Cortes Realizados ao Longo do Tempo por Área")
                ax.grid(True)
                ax.legend(title="Áreas", bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
