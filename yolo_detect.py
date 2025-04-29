from ultralytics import YOLO
import cv2


class Detector:
    def __init__(self, model_name="yolo11n.pt"):
        self.model = YOLO(model_name)

    def detect(self, frame):
        results = self.model(frame)

        detected_objects = results[0].boxes.cls.tolist()
        names = results[0].names

        object_counts = {}
        for obj_id in detected_objects:
            obj_name = names[int(obj_id)]
            object_counts[obj_name] = object_counts.get(obj_name, 0) + 1

        # rank by object counts
        object_counts = sorted(object_counts.items())
        if len(object_counts):
            return object_counts
        else:
            return None

    def __call__(self, frame):
        return self.detect(frame)


def main():
    cap = cv2.VideoCapture(0)
    detector = Detector()

    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)

        print(detector(frame))

        cv2.imshow("yolo11", frame)

        if cv2.waitKey(100) == 27:  # ESC 退出
            break

    cv2.destroyAllWindows()
    cap.release()


if __name__=="__main__":
    main()