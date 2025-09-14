# frozen_string_literal: true

source "https://rubygems.org"

# Поддержка GitHub Pages - использует совместимую версию Jekyll и всех зависимостей
gem "github-pages", group: :jekyll_plugins

# Дополнительные плагины Jekyll (если нужны и не включены в github-pages)
group :jekyll_plugins do
  gem "jekyll-sitemap"
  gem "jekyll-paginate"
end

# Windows и JRuby не включают zoneinfo файлы, поэтому нужно bundled gem tzinfo-data
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# Ускоритель производительности для просмотра каталогов на Windows
gem "wdm", "~> 0.1.1", :platforms => [:mingw, :x64_mingw, :mswin]

# Блокировка `http_parser.rb` gem на JRuby сборки, так как он не имеет поддержки Java
gem "http_parser.rb", "~> 0.6.0", :platforms => [:jruby]