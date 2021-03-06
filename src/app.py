import sys
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QApplication, QLabel, QMainWindow, QAction
from PySide2.QtCore import qApp
from plot_data import ScatterPlotter
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from rule_part_widget import RulePartWidget
from rule_table_widget import RuleTableWidget
from plot_attr_selection_widget import PlotAttrSelectionWidget
from sklearn import datasets
from matplotlib.figure import Figure
import pandas as pd

def load_data():
    df = datasets.load_iris(as_frame=True)['frame']
    df.loc[df['target']==2, 'bin_target'] = 1
    df.loc[df['target']!=2, 'bin_target'] = 0
    return df

def calc_ranges(df, cols):
    ranges = {}
    for col in cols:
        ranges[col] = (df[col].min(), df[col].max())
    return ranges

class MainWindow(QMainWindow):
    
    MAX_RULE_PARTS = 7

    # TODO: Specify in config file
    scatter_cols = ['sepal length (cm)',
        'sepal width (cm)',
        'petal length (cm)',
        'petal width (cm)']

    def plot_scatter(self, cols=None, ax=None):

        if cols is None:
            plt_cols = self.scatter_cols
        else:
            plt_cols = cols

        axes = self.plotter.scatter_rule(plt_cols, self.rules, ax=ax)

    def __init__(self):
        QMainWindow.__init__(self)
        
        self.setWindowTitle("Heuristic Generator")

        self.df = load_data()
        self.ranges = calc_ranges(self.df, self.scatter_cols)
        
        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        self.rule_parts = []

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)

        self.file_menu.addAction(exit_action)

        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        self.layout = QtWidgets.QHBoxLayout(self._main)

        self.setup_ui()

        self.plotter = ScatterPlotter(self.df)
        self.update_plot()

        # Window dimensions
        geometry = qApp.desktop().availableGeometry(self)
        self.resize(geometry.width() * 0.7, geometry.height() * 0.8)

    def setup_ui(self):

        left_col = self.setup_left_col()
        right_col = self.setup_right_col()

        self.layout.addWidget(left_col, stretch=2)
        self.layout.addLayout(right_col, stretch=1)

    def setup_left_col(self):

        col_box = QtWidgets.QGroupBox('Rule and data visualization')
        left_col_layout = QtWidgets.QVBoxLayout()

        # self.fig = self.plot_scatter()
        # self.canvas = FigureCanvas(self.fig)
        # self.addToolBar(NavigationToolbar(self.canvas, self))

        # Create Figure canvas
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.fig.clear()
        self.canvas.updateGeometry()
        
        # Button for applying the rules and updating the plot and stats
        add_rule_btn = QtWidgets.QPushButton('Apply and Update')
        add_rule_btn.clicked.connect(self.update_plot)
        update_btn_layout = QtWidgets.QHBoxLayout()
        update_btn_layout.addStretch(stretch=1)
        update_btn_layout.addWidget(add_rule_btn)
        update_btn_layout.addStretch(stretch=1)

        self.plot_attr_selection = PlotAttrSelectionWidget(parent=self, attributes=self.scatter_cols)
        # self.plot_attr_selection.registerChangeListener(self.update_plot)

        left_col_layout.addWidget(self.canvas, stretch=2)
        left_col_layout.addLayout(update_btn_layout)
        left_col_layout.addWidget(self.plot_attr_selection, stretch=1)
        col_box.setLayout(left_col_layout)

        return col_box

    def update_plot(self):
        plt_cols = self.plot_attr_selection.get_plot_attr()
        self.rules = self.get_rules()
        print(self.rules)
        self.fig.clear()
        # self.canvas.figure.clear()
        if len(plt_cols) > 1:
            ax = self.fig.add_subplot()
            self.canvas.figure.clear()
            self.plot_scatter(cols=plt_cols, ax=ax)
        else:
            pass

        # Update stat table
        stats_df = self.plotter.get_rule_stats()
        print(stats_df)
        self.stat_table.update_table(stats_df)
        
        
        self.canvas.draw_idle()

    def get_rules(self):
        rule_list = []
        for rp in self.rule_parts:
            rule_part_dict = {}
            rule = rp.get_rule()
            rule_part_dict['rule_id'] = rule['rule_id']
            rule_part_dict['rule_attr'] = rule['feature']
            rule_part_dict['attr_min'] = rule['range'][0]
            rule_part_dict['attr_max'] = rule['range'][1]
            rule_list.append(rule_part_dict)
        return rule_list

    def add_rule_part(self):
        n_rule_parts = len(self.rule_parts)
        if n_rule_parts < self.MAX_RULE_PARTS:
            rule_part = RulePartWidget(feature_ranges=self.ranges, rule_number=n_rule_parts+1)
            self.rule_parts.append(rule_part)
            self.rule_part_layout.insertWidget(n_rule_parts, rule_part)

    def initial_stat_table(self):
        # stat df: ['rule_id','confidence','support', 'lift', 'recall', 'tp', 'tn', 'fp', 'fn']
        header = ['Rulepart ID', 'Confidence', 'Support', 'Lift', 'Recall', 'TP', 'TN', 'FP', 'FN']
        data = [
        #   ['Rulepart 1', 0.766, 0.427, 2.297, 'X'],
        #   ['Total Ruleset', 0.766, 0.427, 2.297, 'X']
        ]
        table_df = pd.DataFrame(columns=header,
                                data=data)
        return table_df

    def setup_right_col(self):

        right_col_layout = QtWidgets.QVBoxLayout()
        statistics_box = QtWidgets.QGroupBox('Rule statistics')
        statistics_layout = QtWidgets.QVBoxLayout()
        
        table_df = self.initial_stat_table()
        # rule statistics table
        self.stat_table = RuleTableWidget(table_df)

        statistics_layout.addWidget(self.stat_table)
        statistics_box.setLayout(statistics_layout)

        rule_part_box = QtWidgets.QGroupBox('Rule definition')
        self.rule_part_layout = QtWidgets.QVBoxLayout()
        add_rule_btn = QtWidgets.QPushButton('Add Rule part')
        add_rule_btn.clicked.connect(self.add_rule_part)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch(stretch=1)
        btn_layout.addWidget(add_rule_btn)
        btn_layout.addStretch(stretch=1)
        self.rule_part_layout.addLayout(btn_layout)
        self.rule_part_layout.addStretch(stretch=1)
        rule_part_box.setLayout(self.rule_part_layout)

        right_col_layout.addWidget(statistics_box, stretch=1)
        right_col_layout.addWidget(rule_part_box, stretch=1)

        return right_col_layout

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    # Run the main Qt loop
    sys.exit(app.exec_())