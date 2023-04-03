###
### Author : Swapnil Ashok Jadhav
### Created Date : 28 March 2023
### Project Information
###     Find segments with probable tags associated. 
###     Used faster-rcnn version of implementation for quick exploration using detecto.
###     Currently trained with ~700 original images and ~5k augmented images.
###


from yubiai import FTPHOST, FTPPORT, BASE_PATH
from detecto import core, utils
import os, json, cv2


class YubiDocumentSegmentDetection:
    def __init__(self, segment_model="yubi_document_segmentation_v1", use_gpu=False):
        self.use_gpu = use_gpu
        self.current_path = BASE_PATH
        self.model_folder_name = segment_model
        self.model_folder_path = "%s/models/%s" % (self.current_path, self.model_folder_name)
        self.model_zip_path = "%s/models/" % self.current_path
        self.model_zip_name = "%s.zip" % self.model_folder_name
        self.model_ftp_path = "http://%s:%s/yubi_ds_capability/models/%s" % (FTPHOST, FTPPORT, self.model_zip_name)
        self.verify_model_path_ftp()
        self.model, self.label_id_map = self.load_model(self.model_folder_path)

    def load_model(self, model_path):
        model_checkpoint_path = "%s/model.pth" % model_path
        label_id_map_path = "%s/label_id_map.json" % model_path
        label_id_map = json.load(open(label_id_map_path,'r'))
        model = core.Model.load(model_checkpoint_path, list(label_id_map.keys()))
        return model, label_id_map
        
    def verify_model_path_ftp(self):
        """
        Verify if model folder exists at default path.
        If not then download the same from default ftp location
        """
        model_folder_path = self.model_folder_path
        model_zip_path = self.model_zip_path
        model_zip_name = self.model_zip_name
        model_ftp_path = self.model_ftp_path

        if os.path.exists(model_folder_path):
            print("Model Path exist !!")
        elif os.path.exists(f"{model_zip_path}/{model_zip_name}"):
            print("Model Path exist(ZIP format) !!")
            os.system("cd %s; unzip %s; rm -f %s; cd -;" % (model_zip_path, model_zip_name, model_zip_name))
        else:
            print("Model Path do not exist !!")
            os.system("wget %s -P %s" % (model_ftp_path, model_zip_path))
            os.system("cd %s; unzip %s; rm -f %s; cd -;" % (model_zip_path, model_zip_name, model_zip_name))

    def detect_segments(self, imgpath, prob_threshold=0.0, export_image_with_tags=False, export_image_path=""):
        preds = {}
        image = utils.read_image(imgpath)
        predictions = self.model.predict(image)
        labels, boxes, scores = predictions
        boxes = boxes.tolist()
        scores = scores.tolist()
        for i in range(len(labels)):
            if scores[i] >= prob_threshold:
                preds['seg%d'%(i+1)] = {"label_id":labels[i], "label_name":self.label_id_map[labels[i]], 
                                                "box": boxes[i], "probability": scores[i]}
        if export_image_with_tags is True:
            image = cv2.imread(imgpath)
            for k,v in preds.items():
                label = v['label_name']
                xmin,ymin,xmax,ymax = v['box']
                prob = v['probability']
                if prob > prob_threshold:
                    color = (31,31,255)
                    image = cv2.rectangle(image, (int(xmin), int(ymin)), (int(xmax), int(ymax)), color, 2)
                    boxtext = "%s : %s (%.2f)" % (k, label, prob)
                    cv2.putText(image, boxtext, (int(xmin), int(ymin)), cv2.FONT_HERSHEY_COMPLEX, 0.75, color, 2)
            cv2.imwrite(export_image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        return preds
    
    