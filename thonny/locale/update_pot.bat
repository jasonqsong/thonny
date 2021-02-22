cd ..\..
pybabel extract thonny/ --keywords=tr --output-file thonny/locale/thonny.pot
pybabel update -i thonny/locale/thonny.pot -d thonny/locale -D thonny
pause