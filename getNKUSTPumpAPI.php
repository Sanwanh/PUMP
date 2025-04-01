<?php
//$totalAPIData = "";
$resultData = array();
date_default_timezone_set("Asia/Taipei");

	


////雲科大抽水機(高科大)	
	getnkustAPIData();	
	

ini_set('mssql.charset', 'UTF-8');
$serverName = "(local)\MSSQLSERVER01";  //"localhost";
/* Get UID and PWD from application-specific files.  */  
$uid = "iccl"; 
$pwd = "iccl654321"; 
$connectionInfo = array( "UID"=>$uid,  
                         "PWD"=>$pwd,  
                         "Database"=>"ICCL","characterset"=>"utf-8"); 
$conn = sqlsrv_connect( $serverName, $connectionInfo);  
if( $conn === false )  
{  
     //echo "Unable to connect.</br>";  
     die( print_r( sqlsrv_errors(), true));  
}
$sqlstr = "select distinct dl_no from datalist";
$result = sqlsrv_query($conn, $sqlstr);	

$apicount = count($resultData);
$api2out = array();
while($row = sqlsrv_fetch_array($result)){
	for($i=0; $i<$apicount; $i++){		
		if(trim($resultData[$i]['_id'])==trim($row['dl_no'])){
			array_push($api2out,$resultData[$i]);
			break;  
		}
	}
}	

//echo (json_encode($resultData,JSON_UNESCAPED_UNICODE));
//echo (json_encode($api2out,JSON_UNESCAPED_UNICODE));
echo str_replace("\\/","/",json_encode($api2out,JSON_UNESCAPED_UNICODE));


////雲科大抽水機(高科大)	
function getnkustAPIData(){
	$kcity = "_city";
	$kid = "_id";
	$klat = "_lat";
	$klon = "_lon";
	$korg = "_org";
	$korg_name = "_org_name";
	$kroad = "_road";
	$kstatus = "_status";
	$ktown = "_town";
	$koil = "_oil";
	$koperateat = "operateat";
	$vcity = "";
	$vid = "";
	$vlat = 0.0;
	$vlon = 0.0;
	$vorg = "";
	$vorg_name = "";
	$vroad = "";
	$vstatus = "";
	$vtown = "";
	$voperateat = "";
	global $resultData;
	$APIdata = array();		
	
	$serverName = "(local)\MSSQLSERVER01";  //"120.119.155.138";  
	/* Get UID and PWD from application-specific files.  */  
	$uid = "iccl"; 
	$pwd = "iccl654321"; 
	$connectionInfo = array( "UID"=>$uid, "PWD"=>$pwd,  "Database"=>"ICCL","characterset"=>"utf-8");	  
	/* Connect using SQL Server Authentication. */  
	$conn = sqlsrv_connect( $serverName, $connectionInfo);  
	if( $conn === false )  
{  
     echo "Unable to connect.</br>";  
     die( print_r( sqlsrv_errors(), true));  
}  

	$dataqry = " select gd_lon as lon, 
						gd_lat as lat, 
						gd_status as _status, 
						gd_D as pumpname, 
						gd_E as _oil,
						(replace(gd_date,'/','-')+' '+ gd_time) as trimoperateat,
						(replace(gd_date,'-','/')+' '+ gd_time) as operateat,
						DATEPART(yyyy, gd_date) AS gd_year,
						DATEPART(mm, gd_date) AS gd_month,
						DATEPART(dd, gd_date) AS gd_day ,
						gd_time
						
						from (
							select *,
								row_number() over (partition by gd_d order by (replace([gd_date],
								'-','/')+' '+ [gd_time]) desc) sn 
							from getdata
						) r 
						where r.sn=1 order by pumpname";
	$result = sqlsrv_query($conn, $dataqry);	
	while($row = sqlsrv_fetch_array($result)){
		$APIdata[$klon] = $row["lon"];
		$APIdata[$klat] = $row["lat"];
		
		$APIdata[$koperateat] = $row["operateat"];
		
		//$APIdata[$koperateat] = preg_replace('/\\\\\//', '/', $row["operateat"]);
		
		//$APIdata[$koperateat] = $row["gd_year"].'/'.$row["gd_month"].'/'.$row["gd_day"].' '.$row["gd_time"];
		
		$vstatus = $row["_status"];
		if($row["_oil"] != "1"){
			$voil = "0";
		}else{
			$voil = "1";
		}		
		
		$minutes = (time()-strtotime($row["operateat"])) / 60;
		if((int)$minutes > 30){
			$vstatus = "0";
		}
		$vid = $row["pumpname"];
		switch ($vstatus){  //0=離線、1=待機、2=移動、3=抽水中、4=故障、5=缺油警報
			case "0":
				$APIdata[$kstatus] = "離線";
				$voil = "0";
				break;
			case "1":
				$APIdata[$kstatus] = "待命";
				break;	
			case "2":
				$APIdata[$kstatus] = "運送中";
				break;
			case "3":
				$APIdata[$kstatus] = "抽水中";
				break;
			case "4":
				$APIdata[$kstatus] = "故障"; //"待命";
				break;	
			case "5":
				$APIdata[$kstatus] = "油位低電壓";
				break;		
		}
		switch ($vid){
			case "A1":
				$APIdata[$kid] = "北市-09";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市士林區延平北路7段106巷358號";
				$APIdata[$ktown] = "士林區";
				break;			
			case "A5":
				$APIdata[$kid] = "104-L01";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";				
				break;	
			case "A6":
				$APIdata[$kid] = "104-L02";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;		
			case "A9":
				$APIdata[$kid] = "105-L03";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;		
			case "A10":
				$APIdata[$kid] = "105-L04";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;	
			case "A11":
				$APIdata[$kid] = "105-L05";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市龜山區復興三路247巷30號";
				$APIdata[$ktown] = "龜山區";
				break;	
			case "A12":
				$APIdata[$kid] = "105-L06";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;		
			case "A13":
				$APIdata[$kid] = "105-L07";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;		
			case "A14":
				$APIdata[$kid] = "105-L08";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市龜山區復興三路247巷30號";
				$APIdata[$ktown] = "龜山區";
				break;	
			case "A15":
				$APIdata[$kid] = "105-L09";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A101":
				$APIdata[$kid] = "99-M01";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A102":
				$APIdata[$kid] = "99-M02";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A103":
				$APIdata[$kid] = "99-M03";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A104":
				$APIdata[$kid] = "99-M04";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A106":
				$APIdata[$kid] = "99-M05";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A105":
				$APIdata[$kid] = "99-M06";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A107":
				$APIdata[$kid] = "99-M07";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A108":
				$APIdata[$kid] = "99-M08";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A109":
				$APIdata[$kid] = "99-M09";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A110":
				$APIdata[$kid] = "99-M10";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A111":
				$APIdata[$kid] = "99-M11";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A115":
				$APIdata[$kid] = "99-M15";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A113":
				$APIdata[$kid] = "99-M13";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A114":
				$APIdata[$kid] = "99-M14";
				$APIdata[$kcity] = "桃園市";
				$APIdata[$korg] = "61";
				$APIdata[$korg_name] = "桃園市政府";
				$APIdata[$kroad] = "桃園市政府水務局防汛場";
				$APIdata[$ktown] = "";
				break;
			case "A17":
				$APIdata[$kid] = "花蓮縣-01";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣花蓮市國盛七街1號";
				$APIdata[$ktown] = "花蓮市";
				break;
			case "A18":
				$APIdata[$kid] = "花蓮縣-02";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣吉安鄉南濱路一段531號";
				$APIdata[$ktown] = "吉安鄉";
				break;
			case "A19":
				$APIdata[$kid] = "吉安鄉-03";//"花蓮縣-03";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣吉安鄉中山路三段953巷2號";
				$APIdata[$ktown] = "吉安鄉";
				break;
			case "A20":
				$APIdata[$kid] = "吉安鄉-04";//"花蓮縣-04";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣吉安鄉中山路三段953巷2號";
				$APIdata[$ktown] = "吉安鄉";
				break;	
			case "A21":
				$APIdata[$kid] = "花蓮縣-05";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣吉安鄉中山路三段953巷2號";
				$APIdata[$ktown] = "吉安鄉";
				break;
			case "A22":
				$APIdata[$kid] = "花蓮縣-06";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣鳳林鎮榮開路70號";
				$APIdata[$ktown] = "鳳林鎮";
				break;	
			case "A23":
				$APIdata[$kid] = "花蓮縣-07";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣鳳林鎮榮開路70號";
				$APIdata[$ktown] = "鳳林鎮";
				break;		
			case "A24":
				$APIdata[$kid] = "花蓮縣-08";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣玉里鎮清潔隊";
				$APIdata[$ktown] = "玉里鎮";
				break;	
			case "A25":
				$APIdata[$kid] = "花蓮縣-09";
				$APIdata[$kcity] = "花蓮縣";
				$APIdata[$korg] = "66";
				$APIdata[$korg_name] = "花蓮縣政府";
				$APIdata[$kroad] = "花蓮縣玉里鎮清潔隊";
				$APIdata[$ktown] = "玉里鎮";
				break;
			case "A33":
				$APIdata[$kid] = "北市-01";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市中山區濱江街97號";
				$APIdata[$ktown] = "中山區";
				break;		
			case "A34":
				$APIdata[$kid] = "北市-02";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市中山區濱江街97號";
				$APIdata[$ktown] = "中山區";
				break;	
			case "A35":
				$APIdata[$kid] = "北市-03";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市士林區中山北路6段2巷1號";
				$APIdata[$ktown] = "士林區";
				break;		
			case "A36":
				$APIdata[$kid] = "北市-04";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市士林區中山北路6段2巷1號";
				$APIdata[$ktown] = "士林區";
				break;		
			case "A37":
				$APIdata[$kid] = "北市-05";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市士林區中山北路6段2巷1號";
				$APIdata[$ktown] = "士林區";
				break;		
			case "A38":
				$APIdata[$kid] = "北市-06";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市中山區濱江街97號";
				$APIdata[$ktown] = "中山區";
				break;	
			case "A39":
				$APIdata[$kid] = "北市-07";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市士林區中山北路6段2巷1號";
				$APIdata[$ktown] = "士林區";
				break;		
			case "A40":
				$APIdata[$kid] = "北市-08";
				$APIdata[$kcity] = "台北市";
				$APIdata[$korg] = "68";
				$APIdata[$korg_name] = "臺北市政府";
				$APIdata[$kroad] = "臺北市中山區濱江街97號";
				$APIdata[$ktown] = "中山區";
				break;
			case "A84":
				$APIdata[$kid] = "新竹縣-01";
				$APIdata[$kcity] = "新竹縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "新竹縣政府";
				$APIdata[$kroad] = "桃竹苗水情中心";
				$APIdata[$ktown] = "竹北市";
				break;		
			case "A85":
				$APIdata[$kid] = "新竹縣-02";
				$APIdata[$kcity] = "新竹縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "新竹縣政府";
				$APIdata[$kroad] = "桃竹苗水情中心";
				$APIdata[$ktown] = "竹北市";
				break;
			 case "A86":   
				$APIdata[$kid] = "苗栗縣-04";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A87":   
				$APIdata[$kid] = "苗栗縣-05";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A88":   
				$APIdata[$kid] = "苗栗縣-06";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A89":   
				$APIdata[$kid] = "苗栗縣-07";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A90":   
				$APIdata[$kid] = "苗栗縣-08";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;					
			case "A91":
				$APIdata[$kid] = "苗栗縣-09";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A92":
				$APIdata[$kid] = "頭份鎮-01";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A93":
				$APIdata[$kid] = "頭份鎮-02";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A94":
				$APIdata[$kid] = "頭份鎮-03";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;
			case "A95":
				$APIdata[$kid] = "頭份鎮-04";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;	
			case "A96":
				$APIdata[$kid] = "頭份鎮-05";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;	
			case "A97":
				$APIdata[$kid] = "頭份鎮-06";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;               
			case "A98":
				$APIdata[$kid] = "頭份鎮-07";
				$APIdata[$kcity] = "苗栗縣";
				$APIdata[$korg] = "63";
				$APIdata[$korg_name] = "苗栗縣政府";
				$APIdata[$kroad] = "苗栗市經國路四段867號";
				$APIdata[$ktown] = "苗栗市";
				break;	
			case "A116":
				$APIdata[$kid] = "南投縣-01";
				$APIdata[$kcity] = "南投縣";
				$APIdata[$korg] = "64";
				$APIdata[$korg_name] = "南投縣南投市清潔隊";
				$APIdata[$kroad] = "南投縣南投市嶺興路36號";
				$APIdata[$ktown] = "南投縣";
				break;
			case "A117":
				$APIdata[$kid] = "南投縣-02";
				$APIdata[$kcity] = "南投縣";
				$APIdata[$korg] = "64";
				$APIdata[$korg_name] = "南投縣南投市清潔隊";
				$APIdata[$kroad] = "南投縣南投市嶺興路36號";
				$APIdata[$ktown] = "南投縣";
				break;
			case "A118":
				$APIdata[$kid] = "南投縣-03";
				$APIdata[$kcity] = "南投縣";
				$APIdata[$korg] = "64";
				$APIdata[$korg_name] = "南投縣南投市軍功橋";
				$APIdata[$kroad] = "南投縣南投市軍功橋";
				$APIdata[$ktown] = "南投縣";
				break;
			default:
				$APIdata[$kid] = "";
				break;
		}
		$APIdata[$koil] = $voil;
		$desiredOrder = ["_id", "_lon", "_lat", "_status", "_org", "_org_name", "_city", "_town", "_road", "operateat", "_oil"];
		$orderedData = [];
		foreach ($desiredOrder as $key) {
			$orderedData[$key] = $APIdata[$key] ?? ''; 
		}

		array_push($resultData, $orderedData);
	}
}
	
?>	

	
	
	
	
	
	
	
	