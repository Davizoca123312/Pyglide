
import sys
import os
import json
import subprocess
import atexit
import re
import unicodedata
from PyQt5.QtCore import QUrl, QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QLineEdit, QToolBar, QAction, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWebChannel import QWebChannel

# --- Profile Management ---
PROFILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'profiles'))
PROFILES_FILE = os.path.join(PROFILES_DIR, 'profiles.json')

if not os.path.exists(PROFILES_DIR):
    os.makedirs(PROFILES_DIR)

# --- Start Backend ---
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'search_engine_backend', 'app.py')
kwargs = {}
if sys.platform == "win32":
    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
backend_process = subprocess.Popen([sys.executable, backend_path], **kwargs)

@atexit.register
def terminate_backend():
    backend_process.terminate()
    backend_process.wait()

# --- Backend for JS ---
class Backend(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def _read_profiles(self):
        try:
            if not os.path.exists(PROFILES_FILE) or os.path.getsize(PROFILES_FILE) == 0:
                raise FileNotFoundError
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # CORREÇÃO: Perfil padrão sem acento
            default_data = {'profiles': {'Padrao': {'path': 'padrao', 'avatar': ''}}, 'current': 'Padrao'}
            self._write_profiles(default_data)
            return default_data

    def _write_profiles(self, data):
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @pyqtSlot(result=str)
    def get_profiles(self):
        data = self._read_profiles()
        return json.dumps(data)

    @pyqtSlot(str, str, str)
    def update_profile(self, current_name, new_name, new_avatar):
        # VALIDAÇÃO: Rejeita nomes com acentos
        if not new_name.isascii():
            print(f"Tentativa de renomear perfil para nome com acento rejeitada: {new_name}")
            return

        data = self._read_profiles()
        if current_name in data['profiles'] and new_name:
            profile_data = data['profiles'].pop(current_name)
            profile_data['avatar'] = new_avatar
            data['profiles'][new_name] = profile_data
            if data['current'] == current_name:
                data['current'] = new_name
            self._write_profiles(data)

    @pyqtSlot(str)
    def delete_profile(self, profile_name):
        data = self._read_profiles()
        if profile_name in data['profiles'] and len(data['profiles']) > 1:
            del data['profiles'][profile_name]
            if data['current'] == profile_name:
                data['current'] = list(data['profiles'].keys())[0]
            self._write_profiles(data)

    @pyqtSlot(str)
    def add_profile(self, profile_name):
        # VALIDAÇÃO: Rejeita nomes com acentos
        if not profile_name.isascii():
            print(f"Tentativa de criar perfil com acento rejeitada: {profile_name}")
            return

        data = self._read_profiles()
        if profile_name and profile_name not in data['profiles']:
            safe_name = profile_name.lower().replace(' ', '_')
            profile_path = re.sub(r'[^\w-]', '', safe_name)
            data['profiles'][profile_name] = {'path': profile_path, 'avatar': ''}
            self._write_profiles(data)

    @pyqtSlot(str)
    def select_profile(self, profile_name):
        data = self._read_profiles()
        data['current'] = profile_name
        self._write_profiles(data)
        self.window.start_main_browser(profile_name)

# O resto do arquivo permanece o mesmo...

# --- Profile Selection Window ---
class ProfileSelectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seleção de Perfil - PyGlide")
        self.setGeometry(100, 100, 800, 600)

        self.browser = QWebEngineView()
        self.channel = QWebChannel()
        self.backend = Backend(self)
        self.channel.registerObject('backend', self.backend)
        self.browser.page().setWebChannel(self.channel)

        profile_selector_url = QUrl("http://localhost:5001/profiles")
        self.browser.setUrl(profile_selector_url)
        self.setCentralWidget(self.browser)

    def start_main_browser(self, profile_name):
        self.main_window = MainWindow(profile_name)
        self.main_window.show()
        self.close()

# --- Main Browser Window ---
class WebEngineView(QWebEngineView):
    def createWindow(self, _type):
        return self.window().add_new_tab()

class MainWindow(QMainWindow):
    def __init__(self, profile_name):
        super(MainWindow, self).__init__()
        self.current_profile_name = profile_name
        self.load_profile_data()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        navtb = QToolBar("Navegação")
        self.addToolBar(navtb)

        back_btn = QAction("Voltar", self)
        back_btn.triggered.connect(lambda: self.active_browser().back())
        navtb.addAction(back_btn)

        next_btn = QAction("Avançar", self)
        next_btn.triggered.connect(lambda: self.active_browser().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction("Recarregar", self)
        reload_btn.triggered.connect(lambda: self.active_browser().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction("Início", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Pesquise ou digite um endereço")
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        self.profile_btn = QPushButton(self.current_profile_name)
        self.profile_btn.setDisabled(True)
        navtb.addWidget(self.profile_btn)

        add_tab_btn = QAction("+", self)
        add_tab_btn.triggered.connect(lambda: self.add_new_tab())
        navtb.addAction(add_tab_btn)

        self.add_new_tab(QUrl("http://localhost:5001"), "Página Inicial")

        self.setWindowTitle("PyGlide Browser")
        self.setGeometry(100, 100, 1280, 720)

    def load_profile_data(self):
        with open(PROFILES_FILE, 'r') as f:
            profile_data = json.load(f)
        
        profile_info = profile_data['profiles'][self.current_profile_name]
        profile_storage_path = os.path.join(PROFILES_DIR, profile_info['path'])
        
        if not os.path.exists(profile_storage_path):
            os.makedirs(profile_storage_path)

        self.web_profile = QWebEngineProfile(profile_storage_path, self)

    def active_browser(self):
        return self.tabs.currentWidget()

    def add_new_tab(self, qurl=None, label="Nova Aba"):
        if qurl is None:
            qurl = QUrl("http://localhost:5001")

        browser = WebEngineView()
        page = QWebEnginePage(self.web_profile, browser)
        browser.setPage(page)
        browser.setUrl(qurl)
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda q, browser=browser: self.update_urlbar(q, browser))
        browser.loadFinished.connect(lambda _, browser=browser: self.tabs.setTabText(self.tabs.indexOf(browser), browser.page().title()))
        return browser

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            self.close()
            return
        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        qurl = self.active_browser().url() if self.active_browser() else QUrl()
        self.update_urlbar(qurl, self.active_browser())

    def navigate_home(self):
        self.active_browser().setUrl(QUrl("http://localhost:5001"))

    def navigate_to_url(self):
        text = self.urlbar.text().strip()
        if not text:
            return

        is_url = "." in text and " " not in text

        if is_url:
            q = QUrl(text)
            if q.scheme() == "":
                q.setScheme("http")
            self.active_browser().setUrl(q)
        else:
            # CORREÇÃO: Carrega a página inicial (index.html) com o parâmetro de busca
            url = QUrl("http://localhost:5001")
            url.setQuery(f"q={text}")
            self.active_browser().setUrl(url)

    def update_urlbar(self, q, browser=None):
        if browser != self.active_browser():
            return
        
        if q.host() == 'localhost' and q.port() == 5001 and q.path() in ['/search', '/']:
            self.urlbar.setText("")
        else:
            self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    profile_selector = ProfileSelectionWindow()
    profile_selector.show()
    sys.exit(app.exec_())
