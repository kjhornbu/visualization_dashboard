SET /A rng_num=%RANDOM% * 65535 / 32768 + 8080

start "server" K:/workstation/auxiliary/plotly_test-312-20260212/python.exe K:\workstation\code\analysis\visualization_dashboard\app.py %rng_num% "B:\24.chdi.01-PHASE2\stats\scalar\month_15\Scalar_and_Volume\anovan_0110\Genotype_Sex\Non_Erode\Bilateral\Group_Statistical_Results_Genotype_Sex.csv" "B:\24.chdi.01-PHASE2\stats\scalar\month_15\Scalar_and_Volume\anovan_0110\Genotype_Sex\Non_Erode\Bilateral\Group_Data_Table_Genotype_Sex.csv" "B:\24.chdi.01-PHASE2\stats\scalar\month_15\Scalar_and_Volume\anovan_0110\Genotype_Sex\Non_Erode\Subject_Data_Table.csv"
sleep 2
start "" http://127.0.0.1:%rng_num%/
