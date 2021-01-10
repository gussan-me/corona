import pandas as pd
import streamlit as st
import altair as alt  # グラフを描画するためのパッケージ
import datetime as dt
import calendar

THIS_YEAR = dt.datetime.today().year
THIS_MONTH = dt.datetime.today().month

RANGE_YEAR = list(range(2020, THIS_YEAR + 1))
RANGE_MONTH = list(range(1, 13, 1))

DF_CORONA_JAPAN = pd.read_csv(
    'nhk_news_covid19_prefectures_daily_data.csv')  # コロナウイルス感染者数のデータを読み込む
PREFACTURES = DF_CORONA_JAPAN['都道府県名'].unique()  # セレクトボックス用に都道府県名リストを取得しておく

# 2015年の国勢調査から都道府県別人口DFを獲得
DF_POPURATION = pd.read_csv('population.csv', encoding='cp932')
DF_POPURATION_HEISEI = DF_POPURATION[DF_POPURATION['元号'] == '平成']
DF_POPURATION_HEISEI_LATEST = DF_POPURATION_HEISEI[
    DF_POPURATION_HEISEI['西暦（年）'] == 2015]


def get_last_date(year, month):
    return calendar.monthrange(year, month)[1]


def write_prefacture_graph_title(name, term):
    '''グラフのタイトルと期間を表示'''
    st.write('##  ' + name + 'のコロナウイルス新規感染者発表数')
    st.write('## (' + str(term.start_year) + '/' + str(term.start_month) +
             ' - ' + str(term.end_year) + '/' + str(term.end_month) + ')')


def extract_prefacture_data(df, name):
    '''都道府県を指定して読み込み、結果を返すメソッド'''
    result = df[df['都道府県名'] == name].reset_index(drop=True)
    result['日付'] = pd.to_datetime(result['日付'])
    return result


class PrefactureGraphMaker():
    '''新規感染者のグラフを作成するクラス'''
    def __init__(self, df_prefacture):
        self.df_prefacture = df_prefacture

    def alt_graph(self, term):
        '''指定された期間のコロナウイルス新規感染者のグラフを返すメソッド'''

        start = self.df_prefacture['日付'] >= term.start_datetime
        end = self.df_prefacture['日付'] <= term.end_datetime
        df_term = self.df_prefacture[start == end]  #
        graph_slider = alt.Chart(df_term).mark_bar().encode(
            x='日付', y='各地の感染者数_1日ごとの発表数', color='各地の感染者数_1日ごとの発表数').properties(
                width=800, height=640).configure_axis(labelFontSize=20,
                                                      titleFontSize=20)
        st.altair_chart(graph_slider)

    def get_ndays_cum(self, ndays):
        '''直近ndaysの新規感染者の合計を返すメソッド'''
        return sum(self.df_prefacture.tail(ndays)['各地の感染者数_1日ごとの発表数'])


class TermSelectBox():
    '''表示する期間を選択するテキストボックスを管理するクラス'''
    def __init__(self):
        '''横一列にセレクトボックス配置'''
        self.col1, self.col2, self.col3, self.col4 = st.beta_columns(4)

        self.start_year = self.col1.selectbox(
            'START YEAR',
            RANGE_YEAR,
        )
        # strat_yearに合わせて表示範囲を調整
        self.start_month = self.start_month_range(RANGE_MONTH)
        self.end_year = self.end_year_range(RANGE_YEAR)
        self.end_month = self.end_month_range(RANGE_MONTH)

        # start_year年 / start_month月 / 1日 のdatetime
        self.start_datetime = dt.datetime(self.start_year, self.start_month, 1)
        # end_year / end_month / その月の最終日 のdatetime (最終日は月によって異なるので)
        self.end_datetime = dt.datetime(
            self.end_year, self.end_month,
            get_last_date(self.end_year, self.end_month))

    def start_month_range(self, range_month):
        '''start yearが今年だったら、データが存在する月までしか表示しない'''
        if self.start_year == THIS_YEAR:
            return self.col2.selectbox('START MONTH', RANGE_MONTH[:THIS_MONTH])
        else:
            return self.col2.selectbox('START MONTH', RANGE_MONTH)

    def end_year_range(self, range_year):
        '''年を自動的に期間の初めよりも後にする'''
        return self.col3.selectbox(
            'END YEAR', RANGE_YEAR[RANGE_YEAR.index(self.start_year):])

    def end_month_range(self, range_month):
        '''年を自動的に期間の初めよりも後にする'''
        if self.start_year == THIS_YEAR:
            if self.start_year == self.end_year:
                return self.col4.selectbox(
                    'END MONTH', RANGE_MONTH[self.start_month - 1:THIS_MONTH])
            else:
                return self.col4.selectbox('END MONTH',
                                           RANGE_MONTH[:THIS_MONTH])
        else:
            if self.start_year == self.end_year:
                return self.col4.selectbox('END MONTH',
                                           RANGE_MONTH[self.start_month - 1:])
            else:
                return self.col4.selectbox('END MONTH',
                                           RANGE_MONTH[:THIS_MONTH])


if __name__ == "__main__":
    prefacture_name = st.selectbox('都道府県',
                                   (PREFACTURES))  # 都道府県が選べるセレクトボックスを定義
    df_prefacture = extract_prefacture_data(DF_CORONA_JAPAN,
                                            prefacture_name)  # DFから都道府県データを抽出

    _term_sb = TermSelectBox()  # 期間設定用セレクトボックスを定義

    write_prefacture_graph_title(prefacture_name, _term_sb)  # グラフのタイトルと期間を表示

    gm_n = PrefactureGraphMaker(df_prefacture)  # グラフ描画用インスタンス
    gm_n.alt_graph(_term_sb)  # 期間を与えてグラフを描画

    ndays = st.selectbox("日数", range(1, 31, 1), index=2)
    df_population_prefacture = DF_POPURATION_HEISEI_LATEST[
        DF_POPURATION_HEISEI_LATEST['都道府県名'] == prefacture_name]['人口（総数）']

    st.write('### ここ' + str(ndays) + '日間の' + prefacture_name + 'の新規感染者合計:' +
             str(gm_n.get_ndays_cum(ndays)) + '人')

    ndays_per_population = (gm_n.get_ndays_cum(ndays) /
                            int(df_population_prefacture)) * 100

    st.write('### ' + prefacture_name + 'の人口の' +
             str(ndays_per_population)[:5] + '%(1万あたり約' +
             str(round(ndays_per_population * 100))[:4] + '人)')
