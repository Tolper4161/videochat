import RoomOptionsForm from "../RoomOptionsForm/RoomOptionsForm";
import qrCodeImg from "../../assets/img/qr-code.svg";
import "./RoomOptions.css";
import Button from "../Button/Button";

const RoomOptions = () => {
    return (
        <div className="options" id="options">
            <div className="panel">
                <div className="panel-header">
                    <b className="panel-header__title">My Room</b>
                </div>
                <div className="panel-main">
                    <div className="room-options">
                        <div className="room-options__left">
                            <RoomOptionsForm className="room-options__form" />
                            <div className="room-options__btns">
                                <Button className="room-options-btn" icon="icon-phone" background="green-bg">Start Call</Button>
                                <Button className="room-options-btn" icon="icon-link" background="blue-bg">Copy Invite Link</Button>
                            </div>
                        </div>
                        <div className="room-options__right">
                            <img src={ qrCodeImg } className="room-options__qr" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RoomOptions;
