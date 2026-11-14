import Button from "../../Button/Button";
import ButtonIcon from "../../ButtonIcon/ButtonIcon";
import "./Control.css";

const Control = () => {
    return (
        <div className="panel">
            <div className="control">
                <div className="control__left">
                    <Button className="gray-bg control-btn" icon="icon-link">Copy Link</Button>
                </div>
                <div className="control__mid">
                    <ButtonIcon className="gray-bg control-btn" icon="icon-microphone-mute" />
                    <ButtonIcon className="gray-bg control-btn" icon="icon-video-mute" />
                    <ButtonIcon className="gray-bg control-btn" icon="icon-translation" />
                    <ButtonIcon className="gray-bg control-btn" icon="icon-chat" />
                    <ButtonIcon className="gray-bg control-btn" icon="icon-menu-horizontal" />
                </div>
                <div className="control__right">
                    <ButtonIcon className="red-bg control-btn" icon="icon-phone-disconnected" />
                </div>
            </div>
        </div>
    );
};

export default Control;
