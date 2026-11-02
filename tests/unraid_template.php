<?php
// Read-only compatibility check using installed Unraid helpers. Never execute the result.
$docroot='/usr/local/emhttp';
$subnet=['bridge'=>[], 'host'=>[], 'none'=>[]];
$driver=['bridge'=>'bridge', 'host'=>'host', 'none'=>'none'];
$var=['timeZone'=>'UTC','NAME'=>'phase10-test'];
require "$docroot/plugins/dynamix.docker.manager/include/Helpers.php";
function check($condition,$message) { if(!$condition) throw new RuntimeException($message); }
$path=$argv[1]??'config/unraid-template.xml';
$xml=file_get_contents($path);
$settings=xmlToVar($xml);
check(count($settings['Config'])===10,'Config count: '.count($settings['Config']).' from '.$path);
check(count(array_filter($settings['Config'],fn($c)=>$c['Display']==='always'))===3,'Three basic fields');
check(count(array_filter($settings['Config'],fn($c)=>$c['Display']==='advanced'))===7,'Seven advanced fields');
[$bridge]=xmlToCommand($xml,false);
check(str_contains($bridge,"-p '10310:10300/tcp'"),'Bridge mapping');
check(str_contains($bridge,"'/models':'rw'"),'Writable initialization cache');
foreach(['THREADS','PUID','PGID','MAX_AUDIO_SECONDS','MAX_CONNECTIONS','CLIENT_TIMEOUT_SECONDS','LOG_LEVEL','LOG_TRANSCRIPTS'] as $key) {
 check(str_contains($bridge,"-e '$key'="),"Retained variable $key");
}
foreach(['WYOMING_HOST','WYOMING_PORT','LANGUAGE','STT_DEVICE','MODEL_DIR','ENCODER_PATH','DECODER_PATH','JOINER_PATH','TOKENS_PATH','MAX_AUDIO_CHUNK_BYTES','INFERENCE_CHUNK_MS'] as $key) {
 check(!str_contains($bridge,"-e '$key'="),"Omitted $key");
}
$host=simplexml_load_string($xml);
$host->Network='host';
[$hostcmd]=xmlToCommand($host->asXML(),false);
check(str_contains($hostcmd,"--net='host'"),'Host mode');
check(!str_contains($hostcmd,' -p '),'Host mode does not map ports');
// Model the user's saved custom settings without reading or writing any real template.
$custom=simplexml_load_string($xml);
foreach($custom->Config as $c) if((string)$c['Type']==='Port') $c['Target']='10444';
foreach(['WYOMING_PORT'=>'10444','INFERENCE_CHUNK_MS'=>'80','ENCODER_PATH'=>'/custom/encoder.onnx'] as $key=>$value) {
 $c=$custom->addChild('Config',$value);
 foreach(['Name'=>$key,'Target'=>$key,'Default'=>$value,'Mode'=>'','Description'=>'Manual setting','Type'=>'Variable','Display'=>'advanced','Required'=>'false','Mask'=>'false'] as $k=>$v)$c->addAttribute($k,$v);
}
[$customcmd]=xmlToCommand($custom->asXML(),false);
check(str_contains($customcmd,"-e 'WYOMING_PORT'='10444'"),'Manual port retained');
check(str_contains($customcmd,"-p '10310:10444/tcp'"),'Manual port target matches server');
check(str_contains($customcmd,"-e 'INFERENCE_CHUNK_MS'='80'"),'Manual chunk retained');
check(str_contains($customcmd,"-e 'ENCODER_PATH'='/custom/encoder.onnx'"),'Manual model path retained');
$source=file_get_contents("$docroot/plugins/dynamix.docker.manager/include/CreateDocker.php");
check(str_contains($source, "Opts.Display == 'advanced'"),'Installed UI supports advanced');
check(str_contains($source,'configLocationAdvanced'),'Advanced settings location');
echo json_encode(['status'=>'passed','basic'=>3,'advanced'=>7,'bridge_command'=>$bridge,'host_command'=>$hostcmd,'manual_command'=>$customcmd],JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";
